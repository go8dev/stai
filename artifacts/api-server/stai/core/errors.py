"""One error shape for every failure the API reports.

    {"error": "<stable code>", "message": "<for people>", "correlationId": "<id>", "details": [...]}

Messages are written here, never taken from an exception, so nothing from a stack trace,
a database driver or a secret can reach a response.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from stai.core.logging import StructuredLogger, get_correlation_id

logger = StructuredLogger(__name__)

NO_STORE_HEADERS = {"Cache-Control": "no-store"}


class ErrorResponse(BaseModel):
    """Body of every error response."""

    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(description="Stable machine-readable code.")
    message: str
    correlation_id: str = Field(alias="correlationId")
    details: list[dict[str, Any]] | None = None


class ApiError(Exception):
    """An error with a status, a stable code and a message that is safe to show."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(f"{status_code} {code}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def unauthorized() -> ApiError:
    return ApiError(401, "not_authenticated", "Log in to continue.")


def csrf_failed(message: str = "This request could not be verified. Reload and try again."):
    return ApiError(403, "csrf_failed", message)


def not_found() -> ApiError:
    return ApiError(404, "not_found", "There is nothing at this address.")


def rate_limited(retry_after_seconds: int) -> ApiError:
    return ApiError(
        429,
        "rate_limited",
        "Too many attempts. Wait a minute and try again.",
        headers={"Retry-After": str(retry_after_seconds)},
    )


def database_unavailable() -> ApiError:
    return ApiError(503, "database_unavailable", "The database cannot be reached right now.")


def error_body(
    code: str,
    message: str,
    *,
    correlation_id: str | None = None,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": code,
        "message": message,
        "correlationId": correlation_id or get_correlation_id() or "",
    }
    if details is not None:
        body["details"] = details
    return body


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    correlation_id: str | None = None,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        error_body(code, message, correlation_id=correlation_id, details=details),
        status_code=status_code,
        headers={**NO_STORE_HEADERS, **(headers or {})},
    )


_STATUS_CODES = {
    400: ("bad_request", "The request could not be understood."),
    401: ("not_authenticated", "Log in to continue."),
    403: ("forbidden", "This action is not allowed."),
    404: ("not_found", "There is nothing at this address."),
    405: ("method_not_allowed", "This address does not accept that kind of request."),
    413: ("payload_too_large", "The request is too large."),
    429: ("rate_limited", "Too many attempts. Wait a minute and try again."),
}


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Where and why validation failed, without echoing what was sent."""
    details: list[dict[str, Any]] = []
    for item in exc.errors():
        details.append(
            {
                "location": [str(part) for part in item.get("loc", ())],
                "type": str(item.get("type", "invalid")),
                "message": str(item.get("msg", "Invalid value")),
            }
        )
    return details


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(
            exc.status_code, exc.code, exc.message, details=exc.details, headers=exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            422,
            "validation_failed",
            "Some of the values sent are not valid.",
            details=_safe_validation_details(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            code, message = "internal_error", "Something went wrong on the server."
        else:
            code, message = _STATUS_CODES.get(
                exc.status_code, ("request_failed", "The request could not be completed.")
            )
        # Only headers that describe the protocol are passed on, never the exception's detail.
        headers = {
            name: value
            for name, value in (exc.headers or {}).items()
            if name.lower() in {"allow", "retry-after"}
        }
        return error_response(exc.status_code, code, message, headers=headers)
