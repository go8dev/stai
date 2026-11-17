"""Outermost request handling: correlation ID, access log, response headers, last-resort 500."""

from __future__ import annotations

import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from stai.core.errors import error_response
from stai.core.logging import StructuredLogger, get_correlation_id, set_correlation_id

logger = StructuredLogger("stai.request")

CORRELATION_HEADER = "X-Correlation-ID"

# Every response from this service is API data or a redirect, never a page to render.
_API_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Robots-Tag": "noindex, nofollow",
}
_HSTS = "max-age=31536000"
_QUIET_PATHS = frozenset({"/api/healthz"})


def correlation_id_from_scope(scope: Scope) -> str:
    state = scope.get("state")
    if isinstance(state, dict):
        value = state.get("correlation_id")
        if isinstance(value, str):
            return value
    return get_correlation_id() or ""


class RequestContextMiddleware:
    """Pure ASGI middleware that must be the outermost one.

    It gives each request a correlation ID, adds the ID and the security headers to the
    response, writes one access-log line without the query string, and turns any error
    nothing else handled into the standard 500 body.
    """

    def __init__(self, app: ASGIApp, *, production: bool):
        self.app = app
        self.production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = uuid.uuid4().hex
        scope.setdefault("state", {})["correlation_id"] = correlation_id
        set_correlation_id(correlation_id)

        method = scope.get("method", "")
        path = scope.get("path", "")
        started = time.perf_counter()
        status_code: int | None = None

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = MutableHeaders(scope=message)
                headers[CORRELATION_HEADER] = correlation_id
                for name, value in _API_HEADERS.items():
                    headers[name] = value
                if "cache-control" not in headers:
                    headers["Cache-Control"] = "no-store"
                if self.production:
                    headers["Strict-Transport-Security"] = _HSTS
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception:
            logger.exception("Unhandled error", method=method, path=path)
            if status_code is not None:
                # Part of a response is already on the wire; let the server drop the connection.
                raise
            response = error_response(
                500,
                "internal_error",
                "Something went wrong on the server.",
                correlation_id=correlation_id,
            )
            await response(scope, receive, send_with_headers)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            log = logger.debug if path in _QUIET_PATHS and status_code == 200 else logger.info
            log("request", method=method, path=path, status=status_code, durationMs=duration_ms)
            set_correlation_id(None)
