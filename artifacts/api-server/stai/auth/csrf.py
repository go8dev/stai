"""CSRF protection for requests that change something.

Two independent checks, both required:

1. The request must come from this app's own origin (`Origin`, else `Referer`).
2. The request must carry `X-CSRF-Token`, a value derived from the session token with
   HMAC-SHA256. A page on another site can neither read it nor send a custom header
   without a CORS permission this service never grants.

The session cookie is also `SameSite=Lax`, so browsers do not attach it to cross-site
POST requests in the first place.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from urllib.parse import urlsplit

from stai.core.config import Settings

CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_CONTEXT = b"stai.csrf.v1"


def csrf_token_for(session_token: str) -> str:
    return hmac.new(session_token.encode("utf-8"), _CONTEXT, hashlib.sha256).hexdigest()


def csrf_token_matches(session_token: str, supplied: str | None) -> bool:
    if not supplied:
        return False
    expected = csrf_token_for(session_token)
    return hmac.compare_digest(expected.encode("ascii"), supplied.encode("utf-8", "replace"))


def _is_own_origin(url: str, settings: Settings) -> bool:
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if not parts.netloc or not settings.is_allowed_host(parts.netloc):
        return False
    if parts.scheme == "https":
        return True
    # Plain http is only ever this machine itself, and only outside production.
    return (
        parts.scheme == "http"
        and not settings.is_production
        and parts.hostname in {"localhost", "127.0.0.1"}
    )


def request_is_same_origin(headers: Mapping[str, str], settings: Settings) -> bool:
    """True when `Origin` (or, without it, `Referer`) names one of this app's hosts."""
    origin = headers.get("origin")
    if origin is not None:
        return _is_own_origin(origin.strip(), settings)
    referer = headers.get("referer")
    if referer:
        return _is_own_origin(referer.strip(), settings)
    return False
