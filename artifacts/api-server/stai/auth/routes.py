"""Sign-in, callback, sign-out and current-user routes.

The route names and the flow follow Replit's sign-in instructions. Two behaviours differ
on purpose: only the configured owner's account gets a session, and a failed sign-in
returns to the sign-in screen with a reason instead of silently starting again.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlsplit

from anyio import to_thread
from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse, Response

from stai.audit.chain import canonical_timestamp
from stai.audit.service import EVENT_SIGNIN, EVENT_SIGNIN_REFUSED, EVENT_SIGNOUT, append_event
from stai.auth.cookies import (
    FLOW_CODE_VERIFIER,
    FLOW_NONCE,
    FLOW_RETURN_TO,
    FLOW_STATE,
    SESSION_COOKIE,
    clear_flow_cookies,
    clear_session_cookie,
    read_flow_cookie,
    set_flow_cookie,
    set_session_cookie,
)
from stai.auth.csrf import csrf_token_for
from stai.auth.deps import current_auth
from stai.auth.gate import AuthContext, is_owner, resolve_session
from stai.auth.oidc import IdentityClaims, OidcError, pkce_challenge, random_token
from stai.auth.schemas import AuthUser, AuthUserEnvelope, CsrfToken
from stai.auth.sessions import create_session, delete_session, purge_expired, upsert_user
from stai.core.config import Settings
from stai.core.errors import ApiError, ErrorResponse, database_unavailable, rate_limited
from stai.core.logging import StructuredLogger
from stai.core.runtime import Runtime, get_runtime
from stai.db.session import DATABASE_ERRORS

logger = StructuredLogger(__name__)

router = APIRouter(prefix="/api", tags=["Auth"])

# The web app is served from the root path.
WEB_ROOT = "/"
CALLBACK_PATH = "/api/callback"

_RATE_WINDOW_SECONDS = 60.0
_RETURN_TO_PARAMETER: dict[str, Any] = {
    "name": "returnTo",
    "in": "query",
    "required": False,
    "description": "Path inside the app to open after sign-in. Anything else is ignored.",
    "schema": {"type": "string"},
}


# -- helpers --------------------------------------------------------------------------------


def request_host(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-host")
    raw = forwarded.split(",")[0] if forwarded else request.headers.get("host", "")
    host = raw.strip().lower()
    return host or None


def request_origin(request: Request, settings: Settings) -> str | None:
    """`https://<host>` for a host this app is served from, else None.

    The host comes from request headers, which a caller controls, so it is only used
    after it matched the configured list. It is never taken on trust.
    """
    host = request_host(request)
    if not settings.is_allowed_host(host):
        return None
    return f"https://{host}"


def safe_return_to(value: str | None) -> str:
    """A path inside the web app, or the root. Never another site, never an API route."""
    if not value or len(value) > 512:
        return WEB_ROOT
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        return WEB_ROOT
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        return WEB_ROOT
    try:
        parts = urlsplit(value)
    except ValueError:
        return WEB_ROOT
    if parts.scheme or parts.netloc:
        return WEB_ROOT
    if parts.path == "/api" or parts.path.startswith("/api/"):
        return WEB_ROOT
    return value


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    return request.client.host if request.client else "unknown"


def _within_limits(
    runtime: Runtime, request: Request, name: str, *, per_client: int, overall: int
) -> bool:
    """Per caller first, then for everyone together, so many addresses cannot add up."""
    limiter = runtime.rate_limiter
    if not limiter.allow(
        f"{name}:client:{client_key(request)}",
        limit=per_client,
        window_seconds=_RATE_WINDOW_SECONDS,
    ):
        return False
    return limiter.allow(f"{name}:all", limit=overall, window_seconds=_RATE_WINDOW_SECONDS)


def _back_to_signin(reason: str, **params: str) -> RedirectResponse:
    """Return to the sign-in screen with a reason it knows how to explain."""
    query = urlencode({"signin": reason, **params})
    response = RedirectResponse(f"{WEB_ROOT}?{query}", status_code=302)
    clear_flow_cookies(response)
    return response


def _unknown_host(request: Request) -> ApiError:
    logger.warning(
        "Sign-in route called on a host that is not configured", host=request_host(request)
    )
    return ApiError(400, "unknown_host", "This address is not one STAI is served from.")


def _same_text(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


# -- database work, run in a worker thread --------------------------------------------------


def _record_refusal(runtime: Runtime, account_id: str) -> None:
    with runtime.database.session() as db:
        append_event(
            db,
            event_type=EVENT_SIGNIN_REFUSED,
            actor_type="account",
            actor_id=account_id,
            payload={"reason": "not_owner"},
        )


def _open_session(runtime: Runtime, claims: IdentityClaims, now: datetime) -> str:
    ttl = timedelta(hours=runtime.settings.session_ttl_hours)
    with runtime.database.session() as db:
        purge_expired(db, now)
        user = upsert_user(db, claims, now)
        token, expires_at = create_session(db, user_id=user.id, now=now, ttl=ttl)
        append_event(
            db,
            event_type=EVENT_SIGNIN,
            actor_type="owner",
            actor_id=user.id,
            payload={"sessionExpiresAt": canonical_timestamp(expires_at)},
            occurred_at=now,
        )
    return token


def _close_session(runtime: Runtime, token: str) -> bool:
    """End the session and record it. False when there was no such session."""
    with runtime.database.session() as db:
        user_id = delete_session(db, token)
        if user_id is None:
            return False
        owner = is_owner(user_id, runtime.settings.owner_user_id)
        append_event(
            db,
            event_type=EVENT_SIGNOUT,
            actor_type="owner" if owner else "account",
            actor_id=user_id,
            payload={},
            occurred_at=runtime.now(),
        )
    return True


# -- routes ---------------------------------------------------------------------------------


@router.get(
    "/auth/user",
    operation_id="getCurrentAuthUser",
    summary="Get the currently signed-in owner, if any",
    response_model=AuthUserEnvelope,
    response_description="Auth state resolved.",
)
async def get_current_auth_user(
    request: Request, runtime: Runtime = Depends(get_runtime)
) -> AuthUserEnvelope:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return AuthUserEnvelope(user=None)
    try:
        session_user = await to_thread.run_sync(resolve_session, runtime, token)
    except DATABASE_ERRORS as exc:
        logger.exception("Session lookup failed")
        raise database_unavailable() from exc
    if session_user is None:
        return AuthUserEnvelope(user=None)
    return AuthUserEnvelope(user=AuthUser.from_session(session_user))


@router.get(
    "/login",
    operation_id="beginBrowserLogin",
    summary="Start the browser sign-in flow",
    status_code=302,
    response_class=RedirectResponse,
    responses={302: {"description": "Redirect to the identity provider."}},
    openapi_extra={"parameters": [_RETURN_TO_PARAMETER]},
)
async def begin_browser_login(
    request: Request, runtime: Runtime = Depends(get_runtime)
) -> Response:
    settings = runtime.settings
    if not _within_limits(runtime, request, "login", per_client=10, overall=30):
        return _back_to_signin("rate-limited")

    if runtime.oidc is None or not settings.signin_configured:
        logger.error(
            "Sign-in is not configured",
            hasClientId=bool(settings.repl_id),
            hasOwnerId=bool(settings.owner_user_id),
        )
        return _back_to_signin("not-configured")

    origin = request_origin(request, settings)
    if origin is None:
        raise _unknown_host(request)

    state = random_token()
    nonce = random_token()
    code_verifier = random_token()
    try:
        authorization_url = await runtime.oidc.authorization_url(
            redirect_uri=f"{origin}{CALLBACK_PATH}",
            state=state,
            nonce=nonce,
            code_challenge=pkce_challenge(code_verifier),
        )
    except OidcError as exc:
        logger.error("Sign-in could not start", reason=exc.reason)
        return _back_to_signin("failed")

    response = RedirectResponse(authorization_url, status_code=302)
    set_flow_cookie(response, FLOW_CODE_VERIFIER, code_verifier)
    set_flow_cookie(response, FLOW_NONCE, nonce)
    set_flow_cookie(response, FLOW_STATE, state)
    set_flow_cookie(response, FLOW_RETURN_TO, safe_return_to(request.query_params.get("returnTo")))
    return response


@router.get(
    "/callback",
    operation_id="handleBrowserLoginCallback",
    summary="Complete the browser sign-in flow",
    status_code=302,
    response_class=RedirectResponse,
    responses={302: {"description": "Redirect back into the app."}},
    openapi_extra={
        "parameters": [
            {"name": name, "in": "query", "required": False, "schema": {"type": "string"}}
            for name in ("code", "state", "iss", "error")
        ]
    },
)
async def handle_browser_login_callback(
    request: Request, runtime: Runtime = Depends(get_runtime)
) -> Response:
    settings = runtime.settings
    if not _within_limits(runtime, request, "callback", per_client=10, overall=30):
        return _back_to_signin("rate-limited")

    if runtime.oidc is None or not settings.signin_configured:
        return _back_to_signin("not-configured")

    origin = request_origin(request, settings)
    if origin is None:
        raise _unknown_host(request)

    params = request.query_params
    provider_error = params.get("error")
    if provider_error:
        logger.info("Sign-in ended at the identity provider", providerError=provider_error[:60])
        return _back_to_signin("cancelled" if provider_error == "access_denied" else "failed")

    code_verifier = read_flow_cookie(request, FLOW_CODE_VERIFIER)
    expected_state = read_flow_cookie(request, FLOW_STATE)
    nonce = read_flow_cookie(request, FLOW_NONCE)
    if not (code_verifier and expected_state and nonce):
        logger.warning("Sign-in callback arrived without the browser's flow cookies")
        return _back_to_signin("cookies")

    state = params.get("state")
    if not state or not _same_text(state, expected_state):
        logger.warning("Sign-in failed a check", reason="state_mismatch")
        return _back_to_signin("failed")

    try:
        metadata = await runtime.oidc.metadata()
        issuer = params.get("iss")
        if issuer is None and metadata.iss_parameter_supported:
            raise OidcError("callback_without_iss")
        if issuer is not None and issuer != metadata.issuer:
            raise OidcError("callback_wrong_iss")
        code = params.get("code")
        if not code:
            raise OidcError("callback_without_code")

        id_token = await runtime.oidc.exchange_code(
            code=code, redirect_uri=f"{origin}{CALLBACK_PATH}", code_verifier=code_verifier
        )
        claims = await runtime.oidc.verify_id_token(id_token, nonce=nonce)
    except OidcError as exc:
        logger.warning("Sign-in failed a check", reason=exc.reason)
        return _back_to_signin("failed")

    if not is_owner(claims.subject, settings.owner_user_id):
        logger.warning("Sign-in refused: not the owner's account")
        try:
            await to_thread.run_sync(_record_refusal, runtime, claims.subject)
        except DATABASE_ERRORS:
            # The refusal stands whether or not it could be written down.
            logger.exception("Refused sign-in could not be recorded")
        return _back_to_signin("refused", account=claims.subject)

    try:
        token = await to_thread.run_sync(_open_session, runtime, claims, runtime.now())
    except DATABASE_ERRORS:
        logger.exception("Session could not be created")
        return _back_to_signin("unavailable")

    logger.info("Owner signed in")
    response = RedirectResponse(
        safe_return_to(read_flow_cookie(request, FLOW_RETURN_TO)), status_code=302
    )
    clear_flow_cookies(response)
    set_session_cookie(response, token, settings.session_ttl_hours * 3600)
    return response


@router.get(
    "/logout",
    operation_id="logoutBrowserSession",
    summary="End the session and sign out",
    status_code=302,
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to the identity provider's sign-out page."},
        429: {"model": ErrorResponse, "description": "Too many attempts."},
    },
)
async def logout_browser_session(
    request: Request, runtime: Runtime = Depends(get_runtime)
) -> Response:
    if not _within_limits(runtime, request, "logout", per_client=20, overall=60):
        raise rate_limited(int(_RATE_WINDOW_SECONDS))

    # A link or image on another site must not be able to sign the owner out.
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        logger.info("Sign-out ignored: the request came from another site")
        return RedirectResponse(WEB_ROOT, status_code=302)

    token = request.cookies.get(SESSION_COOKIE)
    if token:
        try:
            if await to_thread.run_sync(_close_session, runtime, token):
                logger.info("Signed out")
        except DATABASE_ERRORS:
            logger.exception("Session could not be ended in the database")
            response = _back_to_signin("signout-failed")
            clear_session_cookie(response)
            return response

    target = WEB_ROOT
    origin = request_origin(request, runtime.settings)
    if origin is not None and runtime.oidc is not None:
        try:
            target = await runtime.oidc.end_session_url(post_logout_redirect_uri=origin) or WEB_ROOT
        except OidcError as exc:
            logger.warning("Provider sign-out page unavailable", reason=exc.reason)

    response = RedirectResponse(target, status_code=302)
    clear_session_cookie(response)
    clear_flow_cookies(response)
    return response


@router.get(
    "/auth/csrf",
    operation_id="getCsrfToken",
    summary="Get the CSRF token for the current session",
    response_model=CsrfToken,
    response_description="Token for the X-CSRF-Token header.",
    responses={401: {"model": ErrorResponse, "description": "Not signed in."}},
)
async def get_csrf_token(auth: AuthContext = Depends(current_auth)) -> CsrfToken:
    return CsrfToken(csrf_token=csrf_token_for(auth.session_token))
