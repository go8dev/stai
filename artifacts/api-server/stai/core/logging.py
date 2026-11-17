"""Structured JSON logs.

One JSON object per line on standard output. Every line written while a request is being
handled carries that request's correlation ID. Two layers keep secrets out:

* fields whose name looks sensitive (token, cookie, password, ...) are replaced, and
* any registered secret value found anywhere in the finished line is masked.
"""

from __future__ import annotations

import json
import logging
import math
import sys
import traceback
from collections.abc import Iterable
from contextvars import ContextVar
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

REDACTED = "[redacted]"

_correlation_id: ContextVar[str | None] = ContextVar("stai_correlation_id", default=None)

_SENSITIVE_NAME_PARTS = (
    "authorization",
    "cookie",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "code_verifier",
    "nonce",
    "email",
    "dsn",
    "database_url",
)

_secret_values: tuple[str, ...] = ()
_MIN_SECRET_LENGTH = 6


def set_correlation_id(value: str | None) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def register_secret_values(values: Iterable[str]) -> None:
    """Remember values to mask in every log line. Very short values are ignored."""
    global _secret_values
    merged = set(_secret_values)
    for value in values:
        if not value or len(value) < _MIN_SECRET_LENGTH:
            continue
        merged.add(value)
        # A line is JSON, so a value holding quotes, backslashes or line breaks appears
        # in its escaped form. Mask that form too.
        merged.add(json.dumps(value, ensure_ascii=False)[1:-1])
    # Longest first, so a secret that contains another one is masked whole.
    _secret_values = tuple(sorted(merged, key=len, reverse=True))


def clear_secret_values() -> None:
    global _secret_values
    _secret_values = ()


def scrub(text: str) -> str:
    """Mask every registered secret value found in `text`."""
    for value in _secret_values:
        if value in text:
            text = text.replace(value, REDACTED)
    return text


def _is_sensitive_name(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in _SENSITIVE_NAME_PARTS)


def _jsonable(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        # NaN and infinity are not JSON. Written as text, the line stays valid for any parser.
        return str(value)
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        return _jsonable(value.value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {
            str(k): (REDACTED if _is_sensitive_name(str(k)) else _jsonable(v))
            for k, v in value.items()
        }
    if isinstance(value, list | tuple | set | frozenset):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item") and callable(value.item):  # numpy scalars
        try:
            return _jsonable(value.item())
        except (TypeError, ValueError):
            pass
    return str(value)


class JsonFormatter(logging.Formatter):
    """Formats a record as one line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        correlation_id = getattr(record, "correlation_id", None) or get_correlation_id()
        if correlation_id:
            entry["correlationId"] = correlation_id

        fields = getattr(record, "stai_fields", None)
        if isinstance(fields, dict):
            for key, value in fields.items():
                name = key if key not in entry else f"field_{key}"
                entry[name] = REDACTED if _is_sensitive_name(key) else _jsonable(value)

        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc, tb = record.exc_info
            entry["excType"] = exc_type.__name__
            entry["exc"] = str(exc)
            entry["traceback"] = "".join(traceback.format_exception(exc_type, exc, tb))

        line = json.dumps(entry, ensure_ascii=False, default=str, allow_nan=True)
        return scrub(line)


class StructuredLogger:
    """Logger whose calls take a message plus keyword fields.

    >>> logger = StructuredLogger(__name__)
    >>> logger.info("Market snapshot computed", symbol="BTC-USDT", rsi=41.2)
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    @property
    def name(self) -> str:
        return self._logger.name

    def _log(self, level: int, message: str, fields: dict[str, Any], *, exc_info: Any = None):
        if self._logger.isEnabledFor(level):
            self._logger.log(level, message, exc_info=exc_info, extra={"stai_fields": fields})

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, fields)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, fields)

    def critical(self, message: str, **fields: Any) -> None:
        self._log(logging.CRITICAL, message, fields)

    def exception(self, message: str, **fields: Any) -> None:
        """Log at error level with the current exception's type, message and traceback."""
        self._log(logging.ERROR, message, fields, exc_info=True)


_HANDLER_MARK = "_stai_json_handler"

# Libraries that log request URLs, SQL text or result rows. They stay at WARNING whatever
# STAI_LOG_LEVEL says, so turning on debug logs cannot copy stored data into the log.
_QUIET_LIBRARY_LOGGERS = ("httpx", "httpcore", "sqlalchemy")


def quiet_library_loggers() -> None:
    for name in _QUIET_LIBRARY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def configure_logging(level: str = "INFO") -> None:
    """Send every logger in the process through the JSON formatter. Safe to call twice."""
    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    setattr(handler, _HANDLER_MARK, True)
    root.addHandler(handler)

    # Uvicorn's own loggers pass their records up instead of printing them unformatted.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True

    quiet_library_loggers()
