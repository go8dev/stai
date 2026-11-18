# ISP V1 prompt review: revised STAI research scope

This brief translates the attached **STAI Master Replit Agent Prompt — Intraday
Structure & Pullback Strategy (ISP v1.0)** into the rules and boundaries approved
for this workspace. It is not an approval of profitability, new exit rules,
portfolio risk, AI spending, proposals, or trade execution.

## What to retain from the V1 prompt

- Use only closed OKX candles and retain the 1h trend / 15m setup timeframes.
- Use a deterministic entry state machine shared with the Market Scanner.
- Keep spot long-only and futures long/short; restrict this pilot to BTC, ETH and
  SOL.
- For ETH and SOL, require the corresponding BTC 1h direction in the same market.
- Keep AI advisory and subordinate to deterministic controls. Never treat an AI
  confidence value as a win probability or execution permission.
- Preserve saved historical inputs and results so each analysis can be reproduced.
- Compare strategies chronologically and keep the out-of-sample period untouched.

## Current approved entry baseline

New Strategy Lab runs use **ema25-pullback-v2**, the same entry state machine
used by the Scanner:

1. Long: closed 1h EMA25 > EMA99 and close > EMA99. Short: inverse.
2. The 15m EMA25/EMA99 stack must agree with the side.
3. The first completed 15m candle that touches its EMA25 and closes on the right
   side of EMA99 becomes the setup anchor.
4. Within the next four completed 15m candles, confirmation must close beyond
   the anchor candle's high/low and current EMA25.
5. Cancel on trend or structure failure, an adverse EMA99 close, missing data,
   or expiry. BTC context must agree for ETH/SOL.
6. EMA7, MACD, RSI, volume, candle patterns, and the legacy 100-point score do
   not gate entries. The selected 70/100 threshold is not applied to this
   strategy because revised score weights are not approved.

The V1 support/resistance engine is **not** added to the entry gates in this
revision. Its confirmed-swing logic, clustering, 0.5 ATR proximity, and
anti-chasing filters are a possible separate challenger after the EMA baseline
has credible historical evidence. Keep that comparison separate; do not silently
change the shared Scanner state machine.

## Limit orders and historical fills

This is a research-only order simulation, not a live order or a Freqtrade bot:

- After scanner confirmation, rest a buy limit at the original pullback candle's
  high for a long, or a sell limit at its low for a short.
- Wait through at most four later completed 15m candles. If none touches the
  limit, record an expired/unfilled order. It is visible but is not a trade and
  is excluded from win rate and P&L.
- A candle touch approximates a complete fill. If the candle opens through the
  limit, use the better opening price. OHLCV cannot reveal queue position,
  partial fills, exact intrabar order, or whether a real order would fill.
- Show the signal time, requested limit, simulated fill, inherited stop and
  target, actual exit price/time, exit reason, fees, funding, and net result.
- If target and stop both touch within one candle, the stop wins. Do not credit
  a target on the fill candle, where OHLC cannot prove target occurred after
  entry. A data gap cancels an unfilled order.

The current inherited exit references remain **under evaluation**, not approved
strategy parameters: stop at EMA99 minus 1.5% for longs / plus 1.5% for shorts;
target at EMA7 × 1.015 for longs / × 0.985 for shorts; maximum hold 60 minutes.
Do not replace these with ATR or fixed risk/reward rules without a separate
owner decision.

Use STAI's fee defaults, not an assumed account tier: spot maker 0.10% / taker
0.15%; futures maker 0.02% / taker 0.05%. Resting entries and take-profit
limits use maker fees; stop-market and time exits use taker fees. Include
returned historical futures funding. Do **not** add separate spread or slippage
charges: the entry and target are explicit limit prices, as requested. Older
saved results preserve their old assumptions and remain readable.

## Historical AI review is not the live trade committee

The requested first AI capability is a user-initiated review of one saved,
immutable backtest. It can comment on segment metrics, a bounded sample of saved
OHLCV candles, and trade/order evidence. Each response is linked to the run's
SHA-256 data fingerprint and includes risks, limitations, and evidence IDs.

This review cannot discover current entries, allocate the paper fund, approve
risk, create proposals, or place orders. The separate live/paper trade-review
workflow remains a later approval-and-risk step and must not be pulled into
Strategy Lab.

AI review stays disabled until the owner explicitly provides all of the
following through Replit Secrets: an enabled switch, a supported model, that
model's input/output token prices, and a per-run and daily USD cap. An existing
`OPENAI_API_KEY` alone is not spending authorization. Before a provider call,
the server checks the estimated run cost and atomically reserves the full
per-run cap against that UTC day's budget. It makes no automatic retry; when a
provider error leaves billing uncertain, the reservation remains held for that
day. No provider call was made as part of this revision.

## Intentionally deferred from the original prompt

- Do not build or gate the EMA baseline with the V1 support/resistance challenger
  until it is separately specified and tested.
- Do not replace the legacy 70-point score with a new score, and do not call any
  confidence a probability of success.
- Do not change fund allocation, risk per trade, size, leverage, stop, target,
  max hold, daily-loss limit, or portfolio exposure.
- Do not connect a scanner candidate to a committee trade recommendation, risk
  allocation, owner approval, proposal, permit, or bot.
- Do not enable paid AI review, production migrations, publishing, or trading
  without separate authorization.
- Treat zero closed trades as insufficient evidence, not a successful result.

## Versioning and interpretation

The order-aware simulation is versioned as
`okx-limit-order-candle-v3`. Older saved runs keep their original engine,
configuration, source candles, fees, and results. Performance differences
between v2 and v3 are not a controlled strategy comparison because the fill and
cost assumptions changed. Compare only runs sharing the same strategy, engine,
data window, and fee assumptions.
