from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from stai.marketdata.mtf import (
    STRATEGY_VERSION,
    TIMEFRAMES,
    _build_zones,
    _indicator_values,
    _opportunity,
    _raw_swings,
    _runs,
    _score,
    _snapshot,
)
from stai.marketdata.okx_market import _utc_bar_aligned
from stai.marketdata.schemas import CandlePoint, MtfIndicatorSnapshot, MtfZone


def candles(
    count: int,
    *,
    interval: timedelta = timedelta(hours=1),
    start: datetime = datetime(2025, 1, 1, tzinfo=UTC),
    closes: list[Decimal] | None = None,
) -> list[CandlePoint]:
    prices = closes or [Decimal(100 + index) for index in range(count)]
    return [
        CandlePoint(
            opened_at=start + index * interval,
            open=prices[index],
            high=prices[index] + Decimal("2"),
            low=prices[index] - Decimal("2"),
            close=prices[index],
            volume=Decimal("1"),
            quote_volume=Decimal("100"),
            complete=True,
        )
        for index in range(count)
    ]


def test_sma_rsi_atr_values_use_closed_contiguous_history() -> None:
    bars = candles(60)
    rsi, sma20, sma50, atr = _indicator_values(bars, timedelta(hours=1))
    assert rsi == 100
    assert sma20 == 149.5
    assert sma50 == 134.5
    assert atr == 4


def test_all_supported_timeframes_align_to_their_utc_intervals() -> None:
    intervals = {
        "1d": timedelta(days=1),
        "4h": timedelta(hours=4),
        "1h": timedelta(hours=1),
        "15m": timedelta(minutes=15),
    }
    start = datetime(2025, 1, 1, tzinfo=UTC)
    for timeframe, interval in intervals.items():
        bars = candles(4, interval=interval, start=start)
        assert len(_runs(bars, interval)) == 1
        misaligned = bars[2].model_copy(
            update={"opened_at": bars[2].opened_at + timedelta(minutes=1)}
        )
        assert len(_runs([*bars[:2], misaligned, bars[3]], interval)) == 3
        if timeframe == "1d":
            assert all(bar.opened_at.hour == 0 for bar in bars)
        assert _utc_bar_aligned(timeframe, bars[0].opened_at)
        assert not _utc_bar_aligned(timeframe, bars[0].opened_at + timedelta(minutes=1))


def test_indicator_warmup_does_not_publish_sma50_early() -> None:
    rsi, sma20, sma50, atr = _indicator_values(candles(49), timedelta(hours=1))
    assert rsi is None
    assert sma20 is None
    assert sma50 is None
    assert atr is None


def test_missing_latest_expected_completed_candle_is_stale() -> None:
    bars = candles(60, interval=timedelta(hours=1))
    now = bars[-1].opened_at + timedelta(hours=2)
    snapshot = _snapshot("1h", bars, now)
    assert snapshot.status == "stale"


def test_missing_history_gap_resets_indicator_warmup_and_is_reported() -> None:
    bars = candles(70)
    bars[55:] = [
        item.model_copy(update={"opened_at": item.opened_at + timedelta(hours=2)})
        for item in bars[55:]
    ]
    snapshot = _snapshot("1h", bars, datetime(2025, 1, 4, tzinfo=UTC))
    assert snapshot.gap_count == 1
    assert snapshot.status == "insufficient"
    assert snapshot.sma50 is None


def test_incomplete_last_candle_is_never_used() -> None:
    bars = candles(61)
    bars[-1] = bars[-1].model_copy(update={"complete": False, "close": Decimal("9999")})
    rsi, sma20, sma50, _ = _indicator_values(bars, timedelta(hours=1))
    assert rsi == 100
    assert sma20 == 149.5
    assert sma50 == 134.5


def test_balanced_scores_keep_neutral_points_and_sum_to_100() -> None:
    snapshots = [
        MtfIndicatorSnapshot(
            timeframe=timeframe,
            status="fresh",
            latest_completed_at=datetime(2025, 1, 1, tzinfo=UTC),
            close=Decimal("100"),
            rsi14=60 if timeframe != "15m" else 50,
            sma20=101,
            sma50=100,
            atr14=1,
            sma_direction="bullish",
            rsi_direction="bullish" if timeframe != "15m" else "neutral",
            candles=[],
            expected_candles=100,
            actual_candles=100,
            gap_count=0,
            detail=None,
        )
        for timeframe in TIMEFRAMES
    ]
    score = _score(snapshots)
    assert score.strategy_version == STRATEGY_VERSION
    assert score.bullish_score == Decimal("87.5")
    assert score.bearish_score == Decimal("0")
    assert score.neutral_points == Decimal("12.5")
    assert score.bullish_score + score.bearish_score + score.neutral_points == 100
    assert score.classification == "strong_bullish"


def test_confirmed_swings_require_two_right_completed_bars() -> None:
    bars = candles(60)
    bars[52] = bars[52].model_copy(update={"low": Decimal("1"), "high": Decimal("200")})
    swings = _raw_swings("1h", bars)
    pivot_time = bars[52].opened_at
    low_swing = next(item for item in swings if item[0] == "support" and item[2] == pivot_time)
    assert low_swing[3] == bars[54].opened_at + timedelta(hours=1)
    truncated = _raw_swings("1h", bars[:54])
    assert not any(item[0] == "support" and item[2] == pivot_time for item in truncated)


def test_score_is_insufficient_when_any_timeframe_is_missing() -> None:
    short = candles(30)
    snapshot = _snapshot("1d", short, datetime(2025, 2, 1, tzinfo=UTC))
    other = [
        MtfIndicatorSnapshot(
            timeframe=timeframe,
            status="insufficient",
            latest_completed_at=None,
            close=None,
            rsi14=None,
            sma20=None,
            sma50=None,
            atr14=None,
            sma_direction="neutral",
            rsi_direction="neutral",
            candles=[],
            expected_candles=0,
            actual_candles=0,
            gap_count=0,
            detail="missing",
        )
        for timeframe in TIMEFRAMES[1:]
    ]
    assert _score([snapshot, *other]).classification == "insufficient"


def test_stale_candles_keep_last_known_scores_but_block_opportunities() -> None:
    snapshots, zones = opportunity_fixture()
    snapshots[0] = snapshots[0].model_copy(update={"status": "stale"})
    evidence = _score(snapshots)
    assert evidence.status == "stale"
    assert evidence.bullish_score == Decimal("100")
    result = _opportunity("futures", evidence, snapshots, zones)
    assert result.state == "insufficient_data"
    assert result.plan is None
    fresh_snapshots, fresh_zones = opportunity_fixture()
    stale_quote = _opportunity(
        "futures", _score(fresh_snapshots), fresh_snapshots, fresh_zones, market_data_fresh=False
    )
    assert stale_quote.state == "insufficient_data"
    assert stale_quote.plan is None


def test_swings_are_not_returned_before_second_right_close() -> None:
    bars = candles(60)
    bars[52] = bars[52].model_copy(update={"low": Decimal("1"), "high": Decimal("250")})
    snapshots = [
        _snapshot(timeframe, bars if timeframe == "1h" else [], datetime(2025, 1, 5, tzinfo=UTC))
        for timeframe in TIMEFRAMES
    ]
    series = {"1d": [], "4h": [], "1h": bars, "15m": []}
    before_confirmation = bars[54].opened_at + timedelta(minutes=59)
    confirmed = bars[54].opened_at + timedelta(hours=1)
    assert not any(
        zone.pivot_at == bars[52].opened_at
        for zone in _build_zones("BTCUSDT", snapshots, series, before_confirmation)
    )
    assert any(
        zone.pivot_at == bars[52].opened_at
        for zone in _build_zones("BTCUSDT", snapshots, series, confirmed)
    )


def test_swing_levels_cluster_with_025_atr_and_transition_when_invalidated() -> None:
    bars = candles(100, closes=[Decimal("100")] * 100)
    bars[52] = bars[52].model_copy(update={"low": Decimal("20")})
    bars[60] = bars[60].model_copy(update={"low": Decimal("20.5")})
    bars[80] = bars[80].model_copy(
        update={
            "low": Decimal("0"),
            "high": Decimal("2"),
            "close": Decimal("1"),
        }
    )
    now = bars[-1].opened_at + timedelta(hours=1)
    snapshots = [
        _snapshot(timeframe, bars if timeframe == "1h" else [], now) for timeframe in TIMEFRAMES
    ]
    zones = _build_zones("BTCUSDT", snapshots, {"1d": [], "4h": [], "1h": bars, "15m": []}, now)
    clustered = next(
        zone
        for zone in zones
        if zone.source_timeframe == "1h"
        and zone.kind == "support"
        and zone.lower < Decimal("21")
        and zone.independent_reactions == 2
    )
    assert clustered.atr_at_calculation is not None
    assert clustered.state == "invalidated"


def test_weekly_extremes_require_all_seven_completed_daily_candles() -> None:
    start = datetime(2025, 1, 13, tzinfo=UTC)
    daily = candles(7, interval=timedelta(days=1), start=start)
    now = start + timedelta(days=7)

    def zones_for(daily_bars):
        snapshots = [
            _snapshot(timeframe, daily_bars if timeframe == "1d" else [], now)
            for timeframe in TIMEFRAMES
        ]
        series = {"1d": daily_bars, "4h": [], "1h": [], "15m": []}
        return _build_zones("BTCUSDT", snapshots, series, now)

    full_week_zones = zones_for(daily)
    assert any(zone.is_prior_extreme and zone.pivot_at == start for zone in full_week_zones)
    partial_week_zones = zones_for(daily[:-1])
    assert not any(zone.is_prior_extreme and zone.pivot_at == start for zone in partial_week_zones)


def test_balanced_score_flags_conflicting_daily_and_intraday_trends() -> None:
    snapshots = [
        MtfIndicatorSnapshot(
            timeframe=timeframe,
            status="fresh",
            latest_completed_at=datetime(2025, 1, 1, tzinfo=UTC),
            close=Decimal("100"),
            rsi14=40,
            sma20=99,
            sma50=100,
            atr14=1,
            sma_direction="bearish",
            rsi_direction="bearish",
            candles=[],
            expected_candles=100,
            actual_candles=100,
            gap_count=0,
            detail=None,
        )
        for timeframe in TIMEFRAMES
    ]
    snapshots[0] = snapshots[0].model_copy(
        update={
            "sma_direction": "bullish",
            "sma20": 101,
            "sma50": 100,
        }
    )
    score = _score(snapshots)
    assert (
        "Daily SMA direction (bullish) conflicts with 1H (bearish)." in score.disagreement_reasons
    )


def test_spot_bearish_direction_never_creates_short_opportunity() -> None:
    snapshots = [
        MtfIndicatorSnapshot(
            timeframe=timeframe,
            status="fresh",
            latest_completed_at=datetime(2025, 1, 1, tzinfo=UTC),
            close=Decimal("100"),
            rsi14=20,
            sma20=99,
            sma50=100,
            atr14=1,
            sma_direction="bearish",
            rsi_direction="bearish",
            candles=[],
            expected_candles=100,
            actual_candles=100,
            gap_count=0,
            detail=None,
        )
        for timeframe in TIMEFRAMES
    ]
    evidence = _score(snapshots)
    result = _opportunity("spot", evidence, snapshots, [])
    assert result.state == "bearish_watchlist"
    assert result.direction is None
    assert result.plan is None


def opportunity_fixture(*, confirmed: bool = True, target_price: Decimal | None = Decimal("125")):
    start = datetime(2025, 2, 1, tzinfo=UTC)
    interval = timedelta(minutes=15)
    prices = [Decimal("110")] * 100
    bars = candles(100, interval=interval, start=start, closes=prices)
    bars[96] = bars[96].model_copy(
        update={
            "low": Decimal("99"),
            "high": Decimal("102"),
            "close": Decimal("100"),
        }
    )
    bars[97] = bars[97].model_copy(
        update={
            "low": Decimal("101"),
            "high": Decimal("104") if confirmed else Decimal("102"),
            "close": Decimal("103") if confirmed else Decimal("101"),
        }
    )
    bars[98] = bars[98].model_copy(
        update={
            "low": Decimal("108"),
            "high": Decimal("112"),
            "close": Decimal("110") if confirmed else Decimal("101"),
        }
    )
    bars[99] = bars[99].model_copy(
        update={
            "low": Decimal("119") if confirmed else Decimal("99"),
            "high": Decimal("121") if confirmed else Decimal("102"),
            "close": Decimal("120") if confirmed else Decimal("101"),
        }
    )
    snapshots = []
    for timeframe in TIMEFRAMES:
        is_m15 = timeframe == "15m"
        snapshots.append(
            MtfIndicatorSnapshot(
                timeframe=timeframe,
                status="fresh",
                latest_completed_at=bars[-1].opened_at + interval if is_m15 else start,
                close=bars[-1].close if is_m15 else Decimal("101"),
                rsi14=60,
                sma20=100,
                sma50=99,
                atr14=1,
                sma_direction="bullish",
                rsi_direction="bullish",
                candles=bars if is_m15 else [],
                expected_candles=100,
                actual_candles=100,
                gap_count=0,
                detail=None,
            )
        )
    confirmed_at = start + timedelta(hours=1)
    zones = [
        MtfZone(
            id="support-zone",
            source_timeframe="1h",
            kind="support",
            lower=Decimal("98"),
            upper=Decimal("100"),
            pivot_at=confirmed_at,
            confirmed_at=confirmed_at,
            atr_at_calculation=Decimal("4"),
            independent_reactions=2,
            state="active",
            distance_from_price=Decimal("20"),
            confluence_timeframes=[],
            is_prior_extreme=False,
            detail="support fixture",
        )
    ]
    if target_price is not None:
        zones.append(
            MtfZone(
                id="resistance-zone",
                source_timeframe="4h",
                kind="resistance",
                lower=target_price,
                upper=target_price + Decimal("2"),
                pivot_at=confirmed_at,
                confirmed_at=confirmed_at,
                atr_at_calculation=Decimal("5"),
                independent_reactions=1,
                state="active",
                distance_from_price=Decimal("5"),
                confluence_timeframes=[],
                is_prior_extreme=False,
                detail="resistance fixture",
            )
        )
    return snapshots, zones


def test_opportunity_requires_closed_candle_confirmation_and_is_deduplicable() -> None:
    snapshots, zones = opportunity_fixture(confirmed=False)
    evidence = _score(snapshots)
    waiting = _opportunity("futures", evidence, snapshots, zones)
    assert waiting.state == "awaiting_confirmation"
    assert waiting.plan is None
    snapshots, zones = opportunity_fixture()
    evidence = _score(snapshots)
    first = _opportunity("futures", evidence, snapshots, zones)
    second = _opportunity("futures", evidence, snapshots, zones)
    assert first.state == "indicative_setup_ready"
    assert first.plan is not None
    assert first.plan.entry_reference == Decimal("103")
    assert first.plan.stop_reference == Decimal("98")
    assert first.plan.target_reference == Decimal("125")
    assert first.plan.price_basis == "indicative_only"
    assert first.anchor_id == second.anchor_id


def test_unavailable_structural_target_never_gets_fabricated() -> None:
    snapshots, zones = opportunity_fixture(target_price=None)
    result = _opportunity("futures", _score(snapshots), snapshots, zones)
    assert result.state == "entry_zone_reached"
    assert result.plan is None


def test_gap_in_recent_15m_window_blocks_research_opportunity() -> None:
    snapshots, zones = opportunity_fixture()
    m15 = snapshots[-1]
    candles_with_gap = list(m15.candles)
    candles_with_gap[-1] = candles_with_gap[-1].model_copy(
        update={"opened_at": candles_with_gap[-1].opened_at + timedelta(minutes=15)}
    )
    snapshots[-1] = m15.model_copy(update={"candles": candles_with_gap})
    result = _opportunity("futures", _score(snapshots), snapshots, zones)
    assert result.state == "insufficient_data"
    assert result.plan is None


def test_four_completed_bars_without_confirmation_expire_the_anchor() -> None:
    snapshots, zones = opportunity_fixture(confirmed=False)
    m15 = snapshots[-1]
    bars = list(m15.candles)
    bars[95] = bars[95].model_copy(
        update={"low": Decimal("99"), "high": Decimal("102"), "close": Decimal("100")}
    )
    for index in range(96, 100):
        bars[index] = bars[index].model_copy(
            update={"low": Decimal("101"), "high": Decimal("103"), "close": Decimal("101")}
        )
    snapshots[-1] = m15.model_copy(update={"candles": bars, "close": Decimal("101")})
    result = _opportunity("futures", _score(snapshots), snapshots, zones)
    assert result.state == "expired"
    assert result.plan is None
