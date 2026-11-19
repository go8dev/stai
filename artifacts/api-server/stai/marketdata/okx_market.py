"""Read-only OKX market data for the scanner and the ported analytics.

Every request is a GET to an explicitly public OKX market-data route. There are
no credentials, private endpoints, or methods that can change an exchange state.
"""

from __future__ import annotations

import asyncio
import math
from collections import OrderedDict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from pydantic import ValidationError

from stai.analytics.schemas.market_data import Candle, Ticker
from stai.core.logging import StructuredLogger
from stai.core.time import utcnow
from stai.marketdata.schemas import (
    BookLevel,
    CandlePoint,
    InstrumentRules,
    MarketScannerRow,
    MarketType,
)

logger = StructuredLogger(__name__)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
MARKET_PATHS = frozenset(
    {
        "/api/v5/market/ticker",
        "/api/v5/market/candles",
        "/api/v5/market/history-candles",
        "/api/v5/market/books",
        "/api/v5/public/instruments",
        "/api/v5/public/funding-rate",
        "/api/v5/public/funding-rate-history",
    }
)
MAX_RESPONSE_BYTES = 1_000_000
STALE_AFTER_SECONDS = 60
_BAR_MS = {
    "1m": 60_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}
# OKX exposes UTC-aligned daily bars separately from its exchange-local 1D bars.
# Use 1Dutc so UTC midnight is validated below rather than silently shifting days.
_BAR_OKX = {"1m": "1m", "15m": "15m", "1h": "1H", "4h": "4H", "1d": "1Dutc"}
_MTF_LIMITS = {"1d": 240, "4h": 240, "1h": 300, "15m": 300}
_MTF_CACHE_TTL = {"1d": 600, "4h": 300, "1h": 120, "15m": 60}


class MarketDataUnavailable(RuntimeError):
    """A public OKX answer was missing or could not be validated."""


def _decimal(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MarketDataUnavailable(f"OKX returned an invalid {field}.") from exc
    if not result.is_finite():
        raise MarketDataUnavailable(f"OKX returned an invalid {field}.")
    return result


def _moment(milliseconds: Any, field: str) -> datetime:
    try:
        value = int(str(milliseconds))
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    except (ValueError, TypeError, OverflowError, OSError) as exc:
        raise MarketDataUnavailable(f"OKX returned an invalid {field}.") from exc


def _utc_bar_aligned(timeframe: str, opened_at: datetime) -> bool:
    if opened_at.tzinfo is None or opened_at.utcoffset() != UTC.utcoffset(opened_at):
        return False
    if timeframe == "1d":
        return opened_at.hour == opened_at.minute == opened_at.second == opened_at.microsecond == 0
    if timeframe == "4h":
        return (
            opened_at.hour % 4 == 0
            and opened_at.minute == opened_at.second == opened_at.microsecond == 0
        )
    if timeframe == "1h":
        return opened_at.minute == opened_at.second == opened_at.microsecond == 0
    if timeframe == "15m":
        return opened_at.minute % 15 == 0 and opened_at.second == opened_at.microsecond == 0
    return False


def _instrument_id(symbol: str, market_type: MarketType) -> str:
    if symbol not in SYMBOLS:
        raise ValueError("Unsupported scanner symbol.")
    base = f"{symbol[:-4]}-USDT"
    return f"{base}-SWAP" if market_type == "futures" else base


class OkxMarketData:
    """Public-data adapter shared by analytics and the Phase 2 Market Scanner."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        *,
        clock=utcnow,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
        concurrency: int = 4,
    ) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._clock = clock
        self._stale_after_seconds = stale_after_seconds
        self._semaphore = asyncio.Semaphore(concurrency)
        self._instrument_cache: dict[str, tuple[datetime, dict[str, InstrumentRules]]] = {}
        self._historical_request_lock = asyncio.Lock()
        self._last_historical_request_at: float | None = None
        self._mtf_candle_cache: OrderedDict[
            tuple[str, MarketType, str], tuple[datetime, list[CandlePoint]]
        ] = OrderedDict()

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        if path not in MARKET_PATHS:
            raise ValueError("Only public OKX market-data routes are allowed.")
        async with self._semaphore:
            try:
                response = await self._http.get(
                    f"{self._base_url}{path}",
                    params=params,
                    headers={"Accept": "application/json"},
                )
            except httpx.HTTPError as exc:
                raise MarketDataUnavailable("OKX public market data could not be reached.") from exc
        if response.status_code != 200:
            raise MarketDataUnavailable(
                f"OKX public market data returned HTTP {response.status_code}."
            )
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise MarketDataUnavailable("OKX public market data response was too large.")
        try:
            payload = response.json()
            if str(payload.get("code")) != "0" or not isinstance(payload.get("data"), list):
                raise MarketDataUnavailable("OKX public market data returned an error.")
            return payload
        except (ValueError, TypeError, AttributeError) as exc:
            raise MarketDataUnavailable(
                "OKX public market data returned an unexpected response."
            ) from exc

    async def _get_historical_page(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """Pace historical endpoint requests across concurrent backtest series."""
        async with self._historical_request_lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            if self._last_historical_request_at is not None:
                delay = 0.12 - (now - self._last_historical_request_at)
                if delay > 0:
                    await asyncio.sleep(delay)
            self._last_historical_request_at = loop.time()
            return await self._get(path, params)

    async def get_ticker(self, symbol: str) -> Ticker | None:
        """Provider implementation used by the existing exchange-neutral analytics."""
        instrument_id = _instrument_id(symbol, "spot")
        try:
            payload = await self._get("/api/v5/market/ticker", {"instId": instrument_id})
            item = payload["data"][0]
            last = _decimal(item["last"], "ticker price")
            open_24h = _decimal(item["open24h"], "24-hour open")
            high = _decimal(item["high24h"], "24-hour high")
            low = _decimal(item["low24h"], "24-hour low")
            change = last - open_24h
            change_pct = Decimal("0") if open_24h == 0 else change / open_24h * 100
            return Ticker(
                symbol=symbol,
                price=float(last),
                change_24h=float(change),
                change_pct_24h=float(change_pct),
                volume=float(_decimal(item["vol24h"], "24-hour volume")),
                quote_volume=float(_decimal(item["volCcy24h"], "24-hour quote volume")),
                high=float(high),
                low=float(low),
                trades=0,
            )
        except (KeyError, IndexError, MarketDataUnavailable):
            logger.warning("OKX ticker unavailable", symbol=symbol)
            return None

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        """Provider implementation used by the existing analytics."""
        if timeframe not in _BAR_OKX or not 1 <= limit <= 300:
            raise ValueError("Unsupported candle timeframe or limit.")
        instrument_id = _instrument_id(symbol, "spot")
        try:
            payload = await self._get(
                "/api/v5/market/candles",
                {"instId": instrument_id, "bar": _BAR_OKX[timeframe], "limit": str(limit)},
            )
            rows = list(reversed(payload["data"]))
            output: list[Candle] = []
            for row in rows:
                opened = _moment(row[0], "candle time")
                volume = _decimal(row[5], "candle volume")
                quote_volume = _decimal(row[7], "candle quote volume")
                output.append(
                    Candle(
                        open_time=int(opened.timestamp() * 1000),
                        open=float(_decimal(row[1], "candle open")),
                        high=float(_decimal(row[2], "candle high")),
                        low=float(_decimal(row[3], "candle low")),
                        close=float(_decimal(row[4], "candle close")),
                        volume=float(volume),
                        close_time=int(opened.timestamp() * 1000) + _BAR_MS[timeframe] - 1,
                        quote_volume=float(quote_volume),
                        trades=0,
                    )
                )
            return output
        except (KeyError, IndexError, MarketDataUnavailable):
            logger.warning("OKX candles unavailable", symbol=symbol, timeframe=timeframe)
            return []

    async def get_historical_candles(
        self,
        symbol: str,
        market_type: MarketType,
        start_at: datetime,
        end_at: datetime,
        *,
        timeframe: str = "15m",
    ) -> list[CandlePoint]:
        """Fetch a bounded, timestamped set of closed OKX historical candles."""
        if (
            symbol not in SYMBOLS
            or market_type not in {"spot", "futures"}
            or timeframe not in _BAR_OKX
        ):
            raise ValueError("Unsupported historical market.")
        if start_at.tzinfo is None or end_at.tzinfo is None or start_at >= end_at:
            raise ValueError("Historical candle bounds must be ordered timezone-aware times.")
        instrument_id = _instrument_id(symbol, market_type)
        start_ms = int(start_at.timestamp() * 1000)
        end_ms = int(end_at.timestamp() * 1000)
        interval_ms = _BAR_MS[timeframe]
        page_limit = 300 if timeframe == "1m" else 100
        page_count = min(
            600,
            max(1, math.ceil((end_ms - start_ms) / (interval_ms * page_limit)) + 2),
        )
        cursor = end_ms
        by_open_time: dict[int, CandlePoint] = {}

        for _ in range(page_count):
            payload = await self._get_historical_page(
                "/api/v5/market/history-candles",
                {
                    "instId": instrument_id,
                    "bar": _BAR_OKX[timeframe],
                    "limit": str(page_limit),
                    "after": str(cursor),
                },
            )
            rows = payload["data"]
            if not rows:
                break
            timestamps: list[int] = []
            for row in rows:
                if len(row) < 9:
                    raise MarketDataUnavailable("OKX historical candle data is incomplete.")
                opened_ms = int(str(row[0]))
                timestamps.append(opened_ms)
                if not start_ms <= opened_ms < end_ms or str(row[8]) != "1":
                    continue
                opened_at = _moment(opened_ms, "historical candle time")
                by_open_time[opened_ms] = CandlePoint(
                    opened_at=opened_at,
                    open=_decimal(row[1], "historical candle open"),
                    high=_decimal(row[2], "historical candle high"),
                    low=_decimal(row[3], "historical candle low"),
                    close=_decimal(row[4], "historical candle close"),
                    volume=_decimal(row[5], "historical candle volume"),
                    quote_volume=_decimal(row[7], "historical candle quote volume"),
                    complete=True,
                )
            oldest_ms = min(timestamps)
            if oldest_ms < start_ms or oldest_ms >= cursor:
                break
            if oldest_ms == start_ms:
                cursor = oldest_ms
                break
            cursor = oldest_ms

        if not by_open_time:
            raise MarketDataUnavailable("OKX returned no closed candles for this period.")
        return [by_open_time[key] for key in sorted(by_open_time)]

    async def get_mtf_candles(
        self, symbol: str, market_type: MarketType, timeframe: str
    ) -> list[CandlePoint]:
        """Return cached, bounded closed history for MTF research only."""
        if timeframe not in _MTF_LIMITS:
            raise ValueError("Unsupported MTF timeframe.")
        key = (symbol, market_type, timeframe)
        now = self._clock()
        cached = self._mtf_candle_cache.get(key)
        if cached and (now - cached[0]).total_seconds() < _MTF_CACHE_TTL[timeframe]:
            self._mtf_candle_cache.move_to_end(key)
            return cached[1]
        interval = _BAR_MS[timeframe]
        end_at = now
        start_at = datetime.fromtimestamp(
            (int(now.timestamp() * 1000) - interval * (_MTF_LIMITS[timeframe] + 2)) / 1000,
            tz=UTC,
        )
        candles = await self.get_historical_candles(
            symbol, market_type, start_at, end_at, timeframe=timeframe
        )
        if any(not _utc_bar_aligned(timeframe, candle.opened_at) for candle in candles):
            raise MarketDataUnavailable(
                f"OKX {timeframe} candles are not aligned to the expected UTC boundary."
            )
        self._mtf_candle_cache[key] = (now, candles)
        self._mtf_candle_cache.move_to_end(key)
        while len(self._mtf_candle_cache) > 24:
            self._mtf_candle_cache.popitem(last=False)
        return candles

    async def get_research_ticker(
        self, symbol: str, market_type: MarketType
    ) -> dict[str, Decimal | datetime]:
        """A public ticker snapshot for the independent read-only MTF response."""
        instrument_id = _instrument_id(symbol, market_type)
        payload = await self._get("/api/v5/market/ticker", {"instId": instrument_id})
        try:
            item = payload["data"][0]
            last = _decimal(item["last"], "ticker price")
            opened = _decimal(item["open24h"], "24-hour open")
            if last <= 0 or opened <= 0:
                raise MarketDataUnavailable("OKX ticker prices are invalid.")
            exchange_at = _moment(item["ts"], "ticker time")
            if (exchange_at - self._clock()).total_seconds() > 5:
                raise MarketDataUnavailable("OKX ticker timestamp is in the future.")
            return {
                "last": last,
                "change_pct_24h": (last - opened) / opened * Decimal("100"),
                "volume_24h": _decimal(item["volCcy24h"], "24-hour quote volume")
                * (last if market_type == "futures" else Decimal("1")),
                "exchange_at": exchange_at,
            }
        except (KeyError, IndexError, TypeError) as exc:
            raise MarketDataUnavailable("OKX returned an incomplete research ticker.") from exc

    async def get_instrument_rule(self, symbol: str, market_type: MarketType) -> InstrumentRules:
        """Return current public instrument rules needed to model one-tick limits."""
        instrument_id = _instrument_id(symbol, market_type)
        rules = await self._instrument_rules(market_type, instrument_id)
        rule = rules.get(instrument_id)
        if rule is None or rule.tick_size is None or rule.tick_size <= 0:
            raise MarketDataUnavailable("OKX did not return a usable instrument tick size.")
        return rule

    async def get_historical_funding(
        self,
        symbol: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[tuple[datetime, Decimal]]:
        """Fetch historical OKX swap funding observations without exchange credentials."""
        if symbol not in SYMBOLS:
            raise ValueError("Unsupported historical market.")
        if start_at.tzinfo is None or end_at.tzinfo is None or start_at >= end_at:
            raise ValueError("Historical funding bounds must be ordered timezone-aware times.")
        instrument_id = _instrument_id(symbol, "futures")
        start_ms = int(start_at.timestamp() * 1000)
        end_ms = int(end_at.timestamp() * 1000)
        cursor = end_ms
        by_funding_time: dict[int, Decimal] = {}

        for _ in range(10):
            payload = await self._get_historical_page(
                "/api/v5/public/funding-rate-history",
                {"instId": instrument_id, "limit": "100", "after": str(cursor)},
            )
            rows = payload["data"]
            if not rows:
                break
            timestamps: list[int] = []
            for row in rows:
                try:
                    funding_ms = int(str(row["fundingTime"]))
                    rate = _decimal(row["fundingRate"], "historical funding rate")
                except (KeyError, TypeError, ValueError) as exc:
                    raise MarketDataUnavailable(
                        "OKX historical funding data is incomplete."
                    ) from exc
                timestamps.append(funding_ms)
                if start_ms <= funding_ms < end_ms:
                    by_funding_time[funding_ms] = rate
            oldest_ms = min(timestamps)
            if oldest_ms <= start_ms or oldest_ms >= cursor:
                break
            cursor = oldest_ms

        return [
            (_moment(timestamp, "historical funding time"), by_funding_time[timestamp])
            for timestamp in sorted(by_funding_time)
        ]

    async def _instrument_rules(
        self, market_type: MarketType, instrument_id: str
    ) -> dict[str, InstrumentRules]:
        now = self._clock()
        cached = self._instrument_cache.get(instrument_id)
        if cached is not None and (now - cached[0]).total_seconds() < 3600:
            return cached[1]
        kind = "SPOT" if market_type == "spot" else "SWAP"
        payload = await self._get(
            "/api/v5/public/instruments", {"instType": kind, "instId": instrument_id}
        )
        wanted = {_instrument_id(symbol, market_type) for symbol in SYMBOLS}
        result: dict[str, InstrumentRules] = {}
        for item in payload["data"]:
            instrument_id = item.get("instId")
            if instrument_id not in wanted:
                continue
            result[instrument_id] = InstrumentRules(
                instrument_id=instrument_id,
                min_size=_decimal(item["minSz"], "minimum size") if item.get("minSz") else None,
                lot_size=_decimal(item["lotSz"], "lot size") if item.get("lotSz") else None,
                tick_size=_decimal(item["tickSz"], "tick size") if item.get("tickSz") else None,
                contract_value=(
                    _decimal(item["ctVal"], "contract value") if item.get("ctVal") else None
                ),
                max_leverage=None,
            )
        self._instrument_cache[instrument_id] = (now, result)
        return result

    async def _row(self, symbol: str, market_type: MarketType) -> MarketScannerRow:
        instrument_id = _instrument_id(symbol, market_type)
        observed_at = self._clock()
        try:
            ticker, candle_data, candle_data_15m, book_data, rules = await asyncio.gather(
                self._get("/api/v5/market/ticker", {"instId": instrument_id}),
                self._get(
                    "/api/v5/market/candles",
                    {"instId": instrument_id, "bar": "1H", "limit": "300"},
                ),
                self._get(
                    "/api/v5/market/candles",
                    {"instId": instrument_id, "bar": "15m", "limit": "300"},
                ),
                self._get("/api/v5/market/books", {"instId": instrument_id, "sz": "5"}),
                self._instrument_rules(market_type, instrument_id),
                return_exceptions=True,
            )
            if any(
                isinstance(result, Exception)
                for result in (ticker, candle_data, candle_data_15m, book_data, rules)
            ):
                raise MarketDataUnavailable("One or more OKX market-data feeds are unavailable.")
            ticker_item = ticker["data"][0]  # type: ignore[index]
            book_item = book_data["data"][0]  # type: ignore[index]
            exchange_at = _moment(ticker_item["ts"], "ticker time")
            book_at = _moment(book_item["ts"], "order book time")
            observed_at = self._clock()
            if any((moment - observed_at).total_seconds() > 5 for moment in (exchange_at, book_at)):
                raise MarketDataUnavailable("Market data timestamp is in the future.")
            exchange_at = min(exchange_at, book_at)
            age = max(0, int((observed_at - exchange_at).total_seconds()))
            status = "fresh" if age <= self._stale_after_seconds else "stale"
            last = _decimal(ticker_item["last"], "ticker price")
            open_24h = _decimal(ticker_item["open24h"], "24-hour open")
            bid = _decimal(ticker_item["bidPx"], "best bid")
            ask = _decimal(ticker_item["askPx"], "best ask")
            if min(last, open_24h, bid, ask) <= 0 or bid >= ask:
                raise MarketDataUnavailable("Market prices are invalid or crossed.")
            change_pct = Decimal("0") if open_24h == 0 else (last - open_24h) / open_24h * 100
            spread = Decimal("0") if last == 0 else (ask - bid) / last * 100
            candles: list[CandlePoint] = []
            for row in reversed(candle_data["data"]):  # type: ignore[index]
                candle_at = _moment(row[0], "candle time")
                candles.append(
                    CandlePoint(
                        opened_at=candle_at,
                        open=_decimal(row[1], "candle open"),
                        high=_decimal(row[2], "candle high"),
                        low=_decimal(row[3], "candle low"),
                        close=_decimal(row[4], "candle close"),
                        volume=_decimal(row[5], "candle volume"),
                        quote_volume=_decimal(row[7], "candle quote volume"),
                        complete=str(row[8]) == "1",
                    )
                )
            candles_15m: list[CandlePoint] = []
            for row in reversed(candle_data_15m["data"]):  # type: ignore[index]
                candle_at = _moment(row[0], "candle time")
                candles_15m.append(
                    CandlePoint(
                        opened_at=candle_at,
                        open=_decimal(row[1], "candle open"),
                        high=_decimal(row[2], "candle high"),
                        low=_decimal(row[3], "candle low"),
                        close=_decimal(row[4], "candle close"),
                        volume=_decimal(row[5], "candle volume"),
                        quote_volume=_decimal(row[7], "candle quote volume"),
                        complete=str(row[8]) == "1",
                    )
                )
            bids = [
                BookLevel(price=_decimal(x[0], "bid price"), size=_decimal(x[1], "bid size"))
                for x in book_item["bids"]
            ]
            asks = [
                BookLevel(price=_decimal(x[0], "ask price"), size=_decimal(x[1], "ask size"))
                for x in book_item["asks"]
            ]
            instrument = rules.get(instrument_id) if isinstance(rules, dict) else None
            if instrument is None or not bids or not asks:
                raise MarketDataUnavailable("Instrument rules or order book are missing.")
            if market_type == "futures":
                if instrument.contract_value is None or instrument.contract_value <= 0:
                    raise MarketDataUnavailable("Contract value is missing.")
                # OKX swap depth is in contracts; the execution estimator uses base units.
                bids = [
                    level.model_copy(update={"size": level.size * instrument.contract_value})
                    for level in bids
                ]
                asks = [
                    level.model_copy(update={"size": level.size * instrument.contract_value})
                    for level in asks
                ]
            for points, interval in ((candles, 3600), (candles_15m, 900)):
                if not points:
                    raise MarketDataUnavailable("Candle data is missing.")
                candle_age = (observed_at - points[-1].opened_at).total_seconds()
                if candle_age < -5 or candle_age > interval * 2:
                    status = "stale"
            funding_rate = None
            next_funding_at = None
            if market_type == "futures":
                funding = await self._get("/api/v5/public/funding-rate", {"instId": instrument_id})
                funding_item = funding["data"][0]
                funding_rate = _decimal(funding_item["fundingRate"], "funding rate")
                next_funding_at = (
                    _moment(funding_item["nextFundingTime"], "next funding time")
                    if funding_item.get("nextFundingTime")
                    else None
                )
            return MarketScannerRow(
                symbol=f"{symbol[:-4]}/USDT",
                market_type=market_type,
                status=status,
                observed_at=observed_at,
                exchange_at=exchange_at,
                age_seconds=age,
                last_price=last,
                change_pct_24h=change_pct,
                volume_24h=(
                    _decimal(ticker_item["volCcy24h"], "24-hour volume")
                    * (last if market_type == "futures" else Decimal("1"))
                ),
                bid=bid,
                ask=ask,
                spread_pct=spread,
                funding_rate=funding_rate,
                next_funding_at=next_funding_at,
                instrument=instrument,
                indicators=None,
                candles=candles,
                candles_15m=candles_15m,
                bids=bids,
                asks=asks,
                detail=(
                    None if status == "fresh" else "Ticker, order book or candle data is stale."
                ),
                setup_scores=None,
                candidate_id=None,
                candidate_status=None,
            )
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            MarketDataUnavailable,
            InvalidOperation,
            ValidationError,
        ) as exc:
            logger.warning(
                "OKX scanner row unavailable",
                symbol=symbol,
                marketType=market_type,
                reason=type(exc).__name__,
            )
            return MarketScannerRow(
                symbol=f"{symbol[:-4]}/USDT",
                market_type=market_type,
                status="unavailable",
                observed_at=observed_at,
                exchange_at=None,
                age_seconds=None,
                last_price=None,
                change_pct_24h=None,
                volume_24h=None,
                bid=None,
                ask=None,
                spread_pct=None,
                funding_rate=None,
                next_funding_at=None,
                instrument=None,
                indicators=None,
                candles=[],
                candles_15m=[],
                bids=[],
                asks=[],
                detail="OKX market data is unavailable for this instrument.",
                setup_scores=None,
                candidate_id=None,
                candidate_status=None,
            )

    async def scanner(self) -> list[MarketScannerRow]:
        rows = await asyncio.gather(
            *(
                self._row(symbol, market_type)
                for symbol in SYMBOLS
                for market_type in ("spot", "futures")
            )
        )
        return list(rows)

    async def latest_snapshot_time(self) -> datetime:
        return self._clock()
