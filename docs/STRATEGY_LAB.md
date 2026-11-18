# Strategy Laboratory

The owner-only `/strategy-lab` page runs deterministic historical research using
public OKX data. It cannot call the AI Committee or create a proposal, permit, or
order. No exchange credentials are used.

## Scanner parity and the known rule conflict

On 18 November 2026, the owner selected **Mirror scanner exactly** after the
conflict was explained:

- A bullish 1h classification requires EMA-7 > EMA-25 > EMA-99 and close > EMA-7,
  but the long pullback gate requires that same close <= EMA-7.
- The bearish/short requirements conflict in reverse.

The laboratory preserves these requirements. It does not silently switch to an
EMA-stack-only trend rule or alter the live scanner. Consequently no eligible
entries are expected. Zero trades leave win rate, expectancy, and profit factor
undefined; they do **not** validate profitability, the inherited stop/target
rules, or the intended 15–60-minute holding period.

## Inputs and reproducibility

- BTC, ETH, or SOL against USDT; spot long and USDT swap long/short are reported
  separately.
- A 7–30-day window ending at the latest closed 15-minute boundary, with seven
  additional warm-up days. Only candles marked closed by OKX are accepted.
- Hourly bars require four consecutive 15-minute candles. Indicators are causal
  and restart after a gap; missing candles are not interpolated.
- The first 70% of time is development and the last 30% is a held-out sample.
  Boundaries are aligned to 15 minutes. No optimization or random split occurs.
- Signals use only completed candles and the latest completed 1h bar. Entries
  use the following 15-minute open; exits cannot cross the holdout boundary.
- Each saved run retains its source candles, historical funding observations,
  query bounds, SHA-256 fingerprint, exact configuration, strategy version, and
  simulation-engine version. Reads are restricted to its owner.

## Hypothetical fills and accounting

This is STAI's closed-candle research simulator, not a Freqtrade execution
backtest. It reuses the scanner's indicator, BTC-regime, scoring, and level
calculations. It does not reproduce live quote freshness, order-book depth,
approval delay, risk vetoes, partial fills, or bot reconciliation.

Each market/side/sample segment starts independently at 1,000 USDT, using a fixed
100 USDT notional at 1x without compounding or overlapping positions. This is not
the live paper fund or its 600/400 allocation. The curve changes at completed
trade exits, so drawdown is closed-trade drawdown, not intrabar mark-to-market.
The inherited stop is EMA-99 ±1.5%; target is EMA-7 ×1.015 for long or ×0.985 for
short. A trade lasts at most four 15-minute bars.

If stop and target both touch one candle, the stop wins. Gaps through a stop or
target use that candle's open where applicable. Intrabar exit time is unknown:
exits are timestamped at candle close, and funding through that timestamp is an
approximation. Incomplete exits at a sample boundary or data gap are excluded.

Taker fees use STAI defaults: spot 0.15% and futures 0.05% per filled notional,
not an account-specific fee tier. Spread and slippage are configurable 0–50 bps
assumptions. Spread charges half the selected bid/ask spread per side; slippage
charges the selected amount per side. Funding uses returned historical rates
on fixed entry notional and is a signed cost (negative means a credit). The
coverage check flags observed gaps over eight hours, including window edges;
it does not prove that every exchange settlement was returned.

Win/loss, expectancy, profit factor, and cumulative performance use net P&L after
these costs. Cumulative return uses the segment's initial 1,000 USDT; per-trade
returns use its 100 USDT notional.

## Verification and operating boundaries

Automated tests cover closed-hour alignment, indicator causality, stop/target
ties, four-bar exits and gaps, fees/funding/spread/slippage, net metrics,
drawdown, pagination and open-candle exclusion, authentication, CSRF, input
validation, persistence, owner-scoped reads, and absence of trade side effects.

A public-data-only BTC smoke check fetched 1,344 spot and 1,344 swap candles
(seven warm-up days plus seven evaluated days), 21 funding observations, and
100% candle coverage for the evaluated window. All six market/side/sample
segments had zero trades, consistent with the preserved conflict. This check
was not saved to the database and made no model calls.

The development schema includes migration `0005_strategy_lab`. No production
migration, publish, paid review, or trading activation is included. Committee
interpretation requires separate authorization of an available model and daily
run/spend limits.
