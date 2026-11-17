"""Cookie names and attributes. Every cookie is httpOnly, Secure and SameSite=Lax."""

from __future__ import annotations

from urllib.parse import quote, unquote

from starlette.requests import Request
from starlette.responses import Response

SESSION_COOKIE = "sid"

# Short-lived values that tie the callback to the browser that started the sign-in.
FLOW_CODE_VERIFIER = "code_verifier"
FLOW_NONCE = "nonce"
FLOW_STATE = "state"
FLOW_RETURN_TO = "return_to"
FLOW_COOKIES = (FLOW_CODE_VERIFIER, FLOW_NONCE, FLOW_STATE, FLOW_RETURN_TO)
FLOW_COOKIE_MAX_AGE_SECONDS = 600
_FLOW_PATH = "/api"


def set_session_cookie(response: Response, token: str, max_age_seconds: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age_seconds,
        path="/",
        httponly=True,
        secure=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=True, samesite="lax")


def set_flow_cookie(response: Response, name: str, value: str) -> None:
    response.set_cookie(
        name,
        quote(value, safe=""),
        max_age=FLOW_COOKIE_MAX_AGE_SECONDS,
        path=_FLOW_PATH,
        httponly=True,
        secure=True,
        samesite="lax",
    )


def read_flow_cookie(request: Request, name: str) -> str | None:
    value = request.cookies.get(name)
    if not value or len(value) > 2048:
        return None
    return unquote(value)


def clear_flow_cookies(response: Response) -> None:
    for name in FLOW_COOKIES:
        response.delete_cookie(name, path=_FLOW_PATH, httponly=True, secure=True, samesite="lax")
