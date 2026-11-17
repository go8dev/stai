"""Deny by default: every address needs the owner's session unless it is listed here.

This is ASGI middleware, not a per-route dependency, so a route added later is closed
without anyone remembering to protect it, and an address that does not exist answers a
signed-out visitor exactly like one that does.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from anyio import to_thread
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from stai.auth.cookies import SESSION_COOKIE
from stai.auth.csrf import CSRF_HEADER, SAFE_METHODS, csrf_token_matches, request_is_same_origin
from stai.auth.sessions import SessionUser, find_session
from stai.core.errors import error_response
from stai.core.logging import StructuredLogger
from stai.core.middleware import correlation_id_from_scope
from stai.core.runtime import Runtime
from stai.db.session import DATABASE_ERRORS

logger = StructuredLogger(__name__)

# The health check and the sign-in routes. Nothing else is reachable while signed out.
PUBLIC_PATHS = frozenset(
    {
        "/api/healthz",
        "/api/login",
        "/api/callback",
        "/api/logout",
        "/api/auth/user",
    }
)


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Who is making this request. Present on every request that passed the gate."""

    user: SessionUser
    session_token: str


def is_owner(user_id: str, owner_user_id: str | None) -> bool:
    if not owner_user_id:
        return False
    return hmac.compare_digest(user_id.encode("utf-8"), owner_user_id.encode("utf-8"))


def resolve_session(runtime: Runtime, token: str | None) -> SessionUser | None:
    """The owner's live session for this cookie value, or None. Reads the database."""
    if not token:
        return None
    with runtime.database.session() as db:
        session_user = find_session(db, token, runtime.now())
    if session_user is None:
        return None
    # Checked on every request, so changing the configured owner locks old sessions out.
    if not is_owner(session_user.user_id, runtime.settings.owner_user_id):
        return None
    return session_user


class AuthGateMiddleware:
    def __init__(self, app: ASGIApp, *, runtime: Runtime):
        self.app = app
        self.runtime = runtime

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return

        if scope["type"] != "http":
            # No WebSocket endpoint exists. Refuse instead of passing it through unchecked.
            await receive()
            await send({"type": "websocket.close", "code": 1008})
            return

        if scope["path"] in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        correlation_id = correlation_id_from_scope(scope)

        async def refuse(status: int, code: str, message: str) -> None:
            response = error_response(status, code, message, correlation_id=correlation_id)
            await response(scope, receive, send)

        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            await refuse(401, "not_authenticated", "Log in to continue.")
            return

        try:
            session_user = await to_thread.run_sync(resolve_session, self.runtime, token)
        except DATABASE_ERRORS:
            logger.exception("Session lookup failed")
            await refuse(503, "database_unavailable", "The database cannot be reached right now.")
            return

        if session_user is None:
            await refuse(401, "not_authenticated", "Log in to continue.")
            return

        if scope["method"] not in SAFE_METHODS:
            if not request_is_same_origin(request.headers, self.runtime.settings):
                logger.warning("Request refused: not from this app's origin", path=scope["path"])
                await refuse(
                    403, "csrf_failed", "This request could not be verified. Reload and try again."
                )
                return
            if not csrf_token_matches(token, request.headers.get(CSRF_HEADER)):
                logger.warning("Request refused: CSRF token missing or wrong", path=scope["path"])
                await refuse(
                    403, "csrf_failed", "This request could not be verified. Reload and try again."
                )
                return

        scope.setdefault("state", {})["auth"] = AuthContext(user=session_user, session_token=token)
        await self.app(scope, receive, send)
