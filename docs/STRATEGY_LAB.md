# Strategy Laboratory

The owner-only `/strategy-lab` page runs deterministic historical research using
public OKX data. It cannot call the AI Committee or create a proposal, permit, or
order. No exchange credentials are used.

## Current entry strategy: EMA25 pullback

New runs use **ema25-pullback-v2**, shared with the Scanner's research evaluator.
The owner approved these entry rules, not a new exit policy or AI/trading activation:

- Long 1h direction: EMA25 > EMA99 and closed price > EMA99. Shorts invert both.
- Long 15m structure: EMA25 > EMA99; short structure is the inverse.
- The first completed 15m candle whose low/high range includes its EMA25 and whose
  close is above EMA99 (long) / below EMA99 (short) starts a setup.
- Within the **next four** consecutive completed 15m candles, a long must close
  above the **original touch candle's high** and current EMA25; a short below
  the original low and current EMA25. Never confirm on the touch candle itself.
- Confirmation can occur on the fourth subsequent candle. Without it the setup
  expires at that candle. Trend/structure failure, an adverse close at or through
  EMA99, missing/unfinished data and gaps cancel the active setup. Equality is not
  directional confirmation. A new touch can start another setup on a later candle.
- ETH/SOL use matching BTC 1h direction in the **same market** (spot or swap).
  BTC uses its own direction once, without a separate composite-regime veto.
- EMA7, MACD, RSI, volume, patterns and the legacy score are **not entry gates**.
  They remain diagnostics. The selected 70/100 future AI threshold has no approved
  revised weights; it is not applied in these historical entry tests.

The Scanner resumes its per-side state from existing market observations under
the scan lock. Stable setup identities include the strategy, instrument, market,
side and original touch timestamp. Reprocessing a completed candle does not emit
another confirmation. No new database table or migration was needed.

Expand a Scanner row to see its version, state, side, original pullback,
confirmation time, setup ID and rule checks. A confirmed candidate remains
**research-only**, with no AI authorization or proposal ID. API and worker scans
use the same resume path; the revised version is blocked from legacy proposals.

## Saved legacy runs and their rule conflict

On 18 November 2026, the owner selected **Mirror scanner exactly** after the
conflict was explained:

- A bullish 1h classification requires EMA-7 > EMA-25 > EMA-99 and close > EMA-7,
  but the long pullback gate requires that same close <= EMA-7.
- The bearish/short requirements conflict in reverse.

Existing **btc-regime-pullback-v1** runs preserve these original requirements
and results; they are never rewritten. Their saved definition still shows the
conflict warning, unlike corrected runs. Consequently no eligible legacy
entries were expected. Zero trades leave win rate, expectancy, and profit factor
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
- Signals use only completed candles and the latest completed 1h bar. New v3
  runs place a resting limit at the original pullback candle's high for longs
  or low for shorts, then wait up to four later completed 15m candles. A candle
  touch is an approximate full fill; a gap through the price receives the
  better opening price. Exits cannot cross the holdout boundary.
- Each saved run retains its source candles, historical funding observations,
  query bounds, SHA-256 fingerprint, exact configuration, strategy version, and
  simulation-engine version. Reads are restricted to its owner.

## Hypothetical fills and accounting

This is STAI's closed-candle research simulator, not a Freqtrade execution
backtest. It shares the versioned entry state machine with the scanner and keeps
the existing indicator and exit-level calculations. It does not reproduce live
quote freshness, order-book depth,
approval delay, risk vetoes, partial fills, or bot reconciliation.

Each market/side/sample segment starts independently at 1,000 USDT, using a fixed
100 USDT notional at 1x without compounding or overlapping positions. There is
one pending entry order or position per segment; signals while it is active are
skipped. Unfilled and cancelled orders are displayed, but are not trades and do
not affect performance metrics. This is not
the live paper fund or its 600/400 allocation. The curve changes at completed
trade exits, so drawdown is closed-trade drawdown, not intrabar mark-to-market.
The inherited stop is EMA-99 ±1.5%; target is EMA-7 ×1.015 for long or ×0.985 for
short. A trade lasts at most four 15-minute bars.
These exits remain inherited and unvalidated, not an approved ATR/2R redesign.
Each segment shows confirmed setups, filled/unfilled/cancelled limit orders,
missing exit indicators, invalid exit geometry and signals skipped while an
order or position is active. Invalid levels are rejected, not changed to force
trades. The trade table shows signal time, requested limit, simulated entry,
stop, target, actual exit price/time, exit reason, fee types, gross/net P&L and
funding. New trade scores are null ("Not applied"), not fabricated confidence
values.

The inherited stop remains EMA-99 minus 1.5% for longs / plus 1.5% for shorts.
The inherited target remains EMA-7 × 1.015 for longs / × 0.985 for shorts. The
stop is simulated as a stop-market exit (taker fee); the target is a limit exit
(maker fee); a 60-minute time exit uses taker fee. These levels and the hold time
remain unvalidated, not an approved ATR/2R redesign.

If stop and target both touch one candle, the stop wins. A target is not credited
on the entry-fill candle because OHLC cannot prove it was touched after entry.
Gaps through a stop or target use that candle's open where applicable. Intrabar
fill and exit times are unknown; fills are timestamped at candle close, and
funding through that timestamp is an approximation. A data gap cancels a resting
unfilled limit. Incomplete exits at a sample boundary or data gap are excluded.
An exit-history gap excludes only that trade; later setups are evaluated after
the bounded holding window and sufficient clean indicator warm-up.

Fee calculations use STAI defaults, not an account-specific OKX tier: spot maker
0.10% / taker 0.15%; futures maker 0.02% / taker 0.05%. There is no separate
spread or slippage charge because the model uses explicit limit prices. Historical
funding uses returned rates on fixed entry notional and is a signed cost (negative
means a credit). The coverage check flags observed gaps over eight hours,
including window edges; it does not prove that every exchange settlement was
returned. Older saved runs keep their original spread/slippage assumptions and
are displayed as legacy results; they are never rewritten.

Win/loss, expectancy, profit factor, and cumulative performance use net P&L after
these costs. Cumulative return uses the segment's initial 1,000 USDT; per-trade
returns use its 100 USDT notional.

## Verification and operating boundaries

Automated tests cover closed-hour alignment, indicator causality, stop/target
ties, four-bar exits and gaps, limit entry touch/expiry, maker/taker fees and
funding, net metrics, drawdown, pagination and open-candle exclusion,
authentication, CSRF, input validation, persistence, owner-scoped reads, and
absence of trade side effects. Historical AI review is manual, attaches to the
saved data fingerprint, uses a bounded sample of OHLCV/trades, and reserves the
per-run amount against a UTC-day budget before calling a provider. The feature
fits all optional samples to one global prompt limit while retaining every
segment's metrics and identifying omitted evidence; populated BTC, ETH and SOL
runs are covered by mocked-provider endpoint tests. The feature
has no model, prices, caps or enable flag configured by default; no AI call is
made until each is explicitly set. Provider failures are never automatically
retried; if billing is unknown, the reservation remains charged against that
day's budget.
The revised-entry checks additionally cover valid long/short sequences, original
touch references, strict confirmation, fourth-bar confirmation/expiry, BTC context,
spot-short exclusion, serialized restart/refresh, scanner/replay parity and legacy
saved-run compatibility. Constructed price waves produce candidates but remain
unfilled when price never revisits the limit; dedicated long/short fixtures check
filled trades. These are functional checks, not evidence of market performance.

A legacy public-data-only BTC smoke check fetched 1,344 spot and 1,344 swap candles
(seven warm-up days plus seven evaluated days), 21 funding observations, and
100% candle coverage for the evaluated window. All six market/side/sample
segments had zero trades, consistent with the preserved conflict. This check
was not saved to the database and made no model calls.

The development schema includes migrations `0005_strategy_lab` and
`0006_strategy_backtest_reviews`. No production migration or publish is included.
Historical AI review, proposals, permits, orders and trading remain disabled
unless separately authorized; this work did not invoke a paid model.
