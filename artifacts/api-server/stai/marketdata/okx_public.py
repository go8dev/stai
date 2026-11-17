"""Reachability check against OKX's public API, without keys.

It answers one question for the system status screen: can this machine reach OKX public
data, and how quickly? That matters at the test publish, because exchanges refuse some
regions. Candles and tickers arrive with the market-data service in Phase 2.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import httpx

from stai.core.logging import StructuredLogger
from stai.core.time import utcnow

logger = StructuredLogger(__name__)

PROVIDER_NAME = "OKX"
TIME_PATH = "/api/v5/public/time"

SLOW_LATENCY_MS = 2000.0
MAX_CLOCK_SKEW_MS = 5000.0
# The real answer is under 100 bytes. Anything much larger is not parsed.
MAX_BODY_BYTES = 4096

Status = Literal["ok", "degraded", "down"]


@dataclass(frozen=True, slots=True)
class MarketDataReachability:
    status: Status
    provider: str
    endpoint: str
    latency_ms: float | None
    exchange_time: datetime | None
    clock_skew_ms: float | None
    checked_at: datetime
    detail: str | None


class OkxPublicProbe:
    """Calls OKX's public server-time endpoint and keeps the answer for a few seconds."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        *,
        clock: Callable[[], datetime] = utcnow,
        cache_seconds: float = 10.0,
        timeout_seconds: float = 8.0,
    ):
        self._http = http
        self._url = f"{base_url.rstrip('/')}{TIME_PATH}"
        self._clock = clock
        self._cache_seconds = cache_seconds
        self._timeout = timeout_seconds
        self._last: MarketDataReachability | None = None
        self._last_at = 0.0

    @property
    def endpoint(self) -> str:
        return self._url

    async def check(self) -> MarketDataReachability:
        now = time.monotonic()
        if self._last is not None and now - self._last_at < self._cache_seconds:
            return self._last
        result = await self._probe()
        self._last, self._last_at = result, time.monotonic()
        if result.status != "ok":
            logger.warning(
                "OKX public data check not ok",
                status=result.status,
                detail=result.detail,
                latencyMs=result.latency_ms,
            )
        return result

    def _result(
        self,
        status: Status,
        *,
        detail: str | None,
        latency_ms: float | None = None,
        exchange_time: datetime | None = None,
        clock_skew_ms: float | None = None,
    ) -> MarketDataReachability:
        return MarketDataReachability(
            status=status,
            provider=PROVIDER_NAME,
            endpoint=self._url,
            latency_ms=latency_ms,
            exchange_time=exchange_time,
            clock_skew_ms=clock_skew_ms,
            checked_at=self._clock(),
            detail=detail,
        )

    async def _probe(self) -> MarketDataReachability:
        sent_at = self._clock()
        started = time.perf_counter()
        try:
            response = await self._http.get(
                self._url, headers={"Accept": "application/json"}, timeout=self._timeout
            )
        except httpx.TimeoutException:
            return self._result(
                "down", detail=f"No answer from OKX within {self._timeout:g} seconds."
            )
        except httpx.HTTPError:
            return self._result("down", detail="OKX could not be reached from this machine.")
        except Exception:
            # Anything else, such as an address that cannot be parsed, is reported the
            # same way instead of failing the status screen. The reason goes to the log.
            logger.exception("OKX public data check could not be run")
            return self._result("down", detail="The OKX check could not be run.")

        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        if response.status_code in (403, 451):
            return self._result(
                "down",
                latency_ms=latency_ms,
                detail=f"OKX answered HTTP {response.status_code}. "
                "This machine's region may be blocked.",
            )
        if response.status_code != 200:
            return self._result(
                "down", latency_ms=latency_ms, detail=f"OKX answered HTTP {response.status_code}."
            )

        try:
            if len(response.content) > MAX_BODY_BYTES:
                raise ValueError("body too large")
            body = response.json()
            code = str(body["code"])
            if code != "0":
                # OKX error codes are short numbers. Anything else is not repeated.
                shown = code if code.isascii() and code.isdigit() and len(code) <= 10 else "unknown"
                return self._result(
                    "down",
                    latency_ms=latency_ms,
                    detail=f"OKX answered with error code {shown}.",
                )
            exchange_ms = int(body["data"][0]["ts"])
            exchange_time = datetime.fromtimestamp(exchange_ms / 1000, tz=UTC)
        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            OverflowError,
            OSError,
            RecursionError,
        ):
            return self._result(
                "down", latency_ms=latency_ms, detail="OKX answered in an unexpected format."
            )

        # Compare OKX's clock with ours at the middle of the round trip.
        local_midpoint_ms = sent_at.timestamp() * 1000 + latency_ms / 2
        clock_skew_ms = round(local_midpoint_ms - exchange_ms, 1)

        if abs(clock_skew_ms) > MAX_CLOCK_SKEW_MS:
            status: Status = "degraded"
            detail: str | None = "This machine's clock and OKX's differ by more than 5 seconds."
        elif latency_ms > SLOW_LATENCY_MS:
            status, detail = "degraded", "OKX answered, but slowly."
        else:
            status, detail = "ok", None

        return self._result(
            status,
            detail=detail,
            latency_ms=latency_ms,
            exchange_time=exchange_time,
            clock_skew_ms=clock_skew_ms,
        )
