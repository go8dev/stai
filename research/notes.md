# Research Notes: STAI Intraday Entry Strategy

**Status:** drafting
**Depth:** Quick

## Plan

- **Question:** What simple OKX intraday setup should screen entry candidates for later Committee review?
- **Scope:** Review the current rule conflict, evidence on intraday trend/pullback designs, trading costs, risk boundaries and backtest validation; do not change code or select parameters from the held-out sample.
- **Audience:** Product owner and engineering team.
- **Deliverable:** A concise, evidence-linked recommendation and an approval boundary for the proposed scanner correction.

## Focus Areas

| # | Area | Status | Sources |
|---|---|---|---|
| 1 | Intraday signal design and independent AI quant-style review | done | 8 |
| 2 | OKX execution costs and risk controls | done | 7 |
| 3 | Backtest validation and timeframe comparison | done | 6 |

## Coverage Checklist

- [ ] State exactly why the current trend and pullback gates cannot both pass.
- [ ] Recommend a simple, causal trend/pullback/confirmation sequence without pretending it is profitable.
- [ ] Compare the plausible 5m, 15m and 4h/15m choices and state data/warm-up constraints.
- [ ] Specify stop, target, maximum holding time, costs, and leverage/risk boundaries that need approval.
- [ ] Keep the 30% holdout protected from choosing among strategies or repeated tuning.
- [ ] Separate the rule screen, advisory Committee review, deterministic risk sizing, and owner approval.

## Findings Log

_[@key] markers reference sources in research/sources.json; they become numbered citations in the final report._

### Intraday signal design and independent quant review

- Research finds both intraday momentum and reversal in crypto; regime dependence and study-specific costs prevent treating either as proof of this setup [@intraday-momentum] [@intraday-reversal] [@bitcoin-technical-rules].
- Independent AI quant-style review: define 1h structure, pullback zone, and next closed 15m confirmation as separate causal rules; no source validates an exact EMA recipe for OKX [@intraday-candles-2026] [@bitcoin-technical-rules].
- The current implementation conflict is confirmed directly in the code at `indicators.py:214-233` and `proposals/service.py:115-139`.

### OKX execution costs and risk controls

- OKX’s current funding rule can vary by instrument and time; align historical rates to actual position exposure and settlement time [@okx-funding] [@okx-api].
- Research and industry guidance support making execution costs and deterministic safeguards explicit; AI remains advisory and cannot set/bypass risk limits [@trading-costs] [@fmsb-ai] [@adaptive-exits].

### Backtest validation and timeframe comparison

- Repeated strategy/timeframe selection can leak information from a nominal holdout; log variants and preserve a final untouched evaluation [@pbo] [@deflated-sharpe] [@oos-methods].
- No source identifies 5m, 15m, or 4h/15m as universally best for this system [@look-ahead-convention] [@intraday-momentum] [@crypto-recent-momentum].

## Conflicts & Open Questions

- The code requires 1h bullish close > EMA-7 while its long pullback gate requires close <= EMA-7; the bearish/short conditions conflict in reverse.
- The owner approved the 1h trend / 15m setup concept and the 70/100 initial score screen, but has not approved the exact corrected formula.
- The current Strategy Laboratory is fixed at 100 USDT notional, 1x, a 30-day maximum, and seven warm-up days; these differ from live paper-fund and risk settings.
- An exact pullback trigger, invalidation window, stop/target formula, and comparison protocol need owner approval before implementation.

## Gaps

- Public studies do not test the exact OKX symbols, fees, timeframe, or proposed rules. Findings are background evidence, not proof of an edge.
- A backtest with no eligible entries cannot estimate win rate or validate stops and targets.
