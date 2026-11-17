"""FastAPI dependencies for routes that need to know who is signed in."""

from __future__ import annotations

from fastapi import Request

from stai.auth.gate import AuthContext
from stai.core.errors import unauthorized


def current_auth(request: Request) -> AuthContext:
    """The owner's session, placed on the request by the gate."""
    auth = getattr(request.state, "auth", None)
    if not isinstance(auth, AuthContext):
        # Only reachable if a route that needs a session was put on the public list.
        raise unauthorized()
    return auth
