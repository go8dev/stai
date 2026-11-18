# STAI: Initial Intraday Strategy Recommendation

**Research Date:** 18 November 2026  
**Depth:** Quick  
**Sources Consulted:** 16 registered sources; 12 cited below. Primary evidence and limitations are identified below.

## Executive Summary

Use a **trend-aligned pullback followed by a completed-candle continuation trigger** as the first strategy to test. Keep the existing 1-hour context and 15-minute decision interval rather than introducing a new timeframe and many new indicators at once. This is a proposed research baseline, not a claim of profitability.

The independent AI quant-style review supported separating trend, pullback and confirmation into distinct rules. It was an AI review, not a consultation with a human or licensed trading adviser. Research documents both momentum and reversal in cryptocurrency markets, with results sensitive to market conditions and the strategy definition. It does not establish that STAI's exact setup has an edge. [1](https://onlinelibrary.wiley.com/doi/full/10.1111/fire.12290) [2](https://www.sciencedirect.com/science/article/pii/S1062940822000833)

The most immediate issue is logical, not statistical: the current long rules require the same hourly close to be above EMA-7 and at-or-below EMA-7. Shorts conflict in reverse. This was checked directly in the current code and is documented in `docs/STRATEGY_LAB.md`. Zero entries therefore do not show whether the intended strategy would win or lose.

The intended product sequence should be: **OKX data → deterministic candidate → advisory AI review → deterministic risk assessment/sizing → owner approval → execution gate**. AI can recommend or challenge a risk treatment; it should not invent an allocation or override hard limits. Independent controls and human accountability are consistent with industry guidance on AI in trading. [3](https://fmsb.com/wp-content/uploads/2026/02/FMSB-AI-in-Trading_Final_12.02.26_FINAL.pdf)

## Background

The owner wants a low-token workflow: software identifies plausible entries using OKX indicators, and only qualifying candidates reach the AI Committee. The existing approved concept is a 1h trend/BTC regime and 15m completed-candle confirmation, with a 70/100 score used for AI eligibility rather than win probability. Spot is long-only; perpetual futures can produce long or short research candidates.

The proposal below changes exact signal semantics and therefore still needs owner approval before implementation. No scanner, Committee automation, production migration, or trading behavior was changed during this research.

The current laboratory is a closed-candle research simulator. Its fixed 100 USDT, 1x trades, 7–30-day window, fee defaults and simplified fills are not a simulation of every live paper-fund control. Those limits matter when interpreting results. In particular, a nominally profitable signal simulation would not prove that a delayed AI-reviewed and owner-approved workflow can obtain the same fills.

## Key Findings

### 1. There is a reasonable hypothesis to test, but no proven recipe

Peer-reviewed research finds intraday Bitcoin momentum and also intraday reversal. These findings concern specific datasets, horizons and mechanisms; neither result validates a particular EMA-7/25/99 rule on OKX. A study of 75,360 Bitcoin technical rules explicitly considered transaction costs, multiple testing and out-of-sample performance, illustrating why a plausible indicator combination alone is insufficient. [1](https://onlinelibrary.wiley.com/doi/full/10.1111/fire.12290) [2](https://www.sciencedirect.com/science/article/pii/S1062940822000833) [4](https://www.sciencedirect.com/science/article/pii/S1059056024003010)

A 2026 candlestick study examined hourly data and many patterns with data-snooping controls, but explicitly omitted transaction costs from its performance evaluation. It is evidence about pattern predictability under those assumptions, not executable net profitability for STAI. Adding named candle patterns or extra indicators should not be treated as an automatic improvement. [5](https://www.sciencedirect.com/science/article/pii/S1059056026002716)

The practical recommendation is to begin with a small causal sequence: identify direction, observe a temporary counter-trend move, then wait for evidence of resumption. Do not demand the pullback and full price recovery on the same hourly candle.

| Candidate | Proposed research role | Main limitation |
|---|---|---|
| 1h context / 15m entry | First baseline; preserves the owner's concept | Exact edge remains untested |
| 1h context / 5m entry | Later comparison, not a silent substitution | Needs finer data and a cost-sensitive execution model |
| 4h context / 15m entry | Later, slower-context comparison | Needs substantially more warm-up and enough independent episodes |

These are engineering/research judgments, not evidence that 15m is universally best. The referenced studies use different horizons and cannot settle this choice for STAI. [1](https://onlinelibrary.wiley.com/doi/full/10.1111/fire.12290) [2](https://www.sciencedirect.com/science/article/pii/S1062940822000833)

### 2. Proposed baseline rules must be explicit and sequential

The following numbers are proposed starting test settings, not optimized parameters and not values endorsed by a cited study.

| Stage | Long setup | Short setup |
|---|---|---|
| 1h direction | EMA7 > EMA25 > EMA99; hourly close > EMA99 | EMA7 < EMA25 < EMA99; hourly close < EMA99 |
| BTC context | Same directional 1h structural rule on BTC; no separate duplicate BTC veto when BTC itself is tested | Inverse direction |
| 15m structure | EMA25 > EMA99 | EMA25 < EMA99 |
| Pullback | A completed 15m candle's range intersects its EMA7–EMA25 band and closes above EMA99 | Same band intersection; closes below EMA99 |
| Subsequent trigger | Within the next four completed 15m bars, close > previous bar's high and close > EMA7 | Close < previous bar's low and close < EMA7 |
| Invalidation | Cancel if 1h direction/BTC context fails, a 15m close crosses EMA99 adversely, or trigger window expires | Mirror long |

Use completed bars only. The pullback must precede the trigger; do not use the eventual trigger bar to retroactively mark the setup. Maintain one active setup per instrument/side and consume it once triggered; no repeated AI calls for the same setup. EMA band intersection means `low <= max(EMA7, EMA25)` and `high >= min(EMA7, EMA25)`.

For an initial reproducible exit hypothesis: stop below the lowest low from the pullback through the trigger, minus 0.25 × ATR(14) on 15m; mirror above the highest high for shorts. Set the gross target to 2R and the maximum holding period to four 15m bars. Reject invalid or unexecutable levels. These choices deliberately remain hypotheses: research on volatility-adaptive exits finds conditional effectiveness in a different market, not universal superiority or crypto validation. [6](https://www.mdpi.com/1911-8074/19/8/554)

For historical tests, enter at the next available 15m open with adverse execution costs and calculate R from that assumed fill. If a gap has already crossed the planned stop, reject the entry instead of fabricating a favorable fill. If both stop and target touch within one OHLC bar, use the conservative stop-first convention unless finer data resolves order.

MACD, volume and the other existing indicators can be recorded as diagnostic evidence initially. Do not add them all as mandatory gates or quietly reuse a score whose definitions no longer match. The 70/100 eligibility score needs a documented mapping consistent with the approved corrected rules before AI automation.

### 3. Execution and risk controls determine whether a candidate is usable

Perpetual funding can debit or credit a position. OKX's settlement interval can vary, and its current documentation is not a substitute for historical instrument-specific records. Model each actual funding assessment during exposure. Fees, spread and additional slippage must also be separate, consistently applied assumptions; avoid charging spread twice if fills already use bid/ask prices. [7](https://www.okx.com/en-us/help/perps-funding-fee-mechanism) [8](https://www.okx.com/docs-v5/en/) [9](https://www.sciencedirect.com/science/article/abs/pii/S0165176522001720)

Compute size from an approved loss budget and stop distance, including costs, then constrain it by available allocation, notional caps, leverage/margin rules and correlated exposure. Leverage changes required margin for a given notional; it is not an instruction to multiply the risk budget or an assurance against liquidation. Stop-based planned loss is not a guaranteed maximum realized loss.

The Committee should return a structured **support / reject / insufficient evidence** assessment, with contrary evidence and uncertainty. The risk engine calculates the final permissible size. Any Committee suggestion to reduce size can be considered within the rules; increasing limits must never happen implicitly. Human accountability and independent controls are central recommendations of the FMSB review. [3](https://fmsb.com/wp-content/uploads/2026/02/FMSB-AI-in-Trading_Final_12.02.26_FINAL.pdf)

## Analysis

The first decision is not “which indicator guarantees more wins?” It is “which precise, falsifiable entry hypothesis will we test?” The proposed baseline keeps the existing conceptual direction while repairing the impossible conjunction. This minimizes simultaneous changes and makes rejection reasons understandable.

The Committee is a second assessment layer, not proof that a signal is correct. Its incremental benefit needs separate measurement: compare all rule-qualified candidates against the subset supported by AI, net of model cost and decision delay. Record rejected and abstained candidates too; otherwise only observing approved trades creates a misleading picture. This is a proposed evaluation design, not a finding that AI improves returns.

For token control, create a compact immutable evidence packet once per new setup: instrument/side, completed-bar timestamps, strategy version, rule outcomes, score components, proposed levels, cost assumptions, BTC context and relevant historical research summaries. Cache unchanged evidence and do not send the whole candle history on every refresh. No paid automation should start until separate daily run/spend limits are approved.

Treat timeframe, stop, target and filter variants as research trials. Develop on earlier chronological data, then freeze the full specification before inspecting a final evaluation period. Selecting whichever candidate looks best on the same “holdout” turns that period into selection data. The PBO and Deflated Sharpe papers explain why multiple testing and short/noisy samples inflate apparent performance. [10](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) [11](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

A synthetic-environment comparison of validation methods does not establish a universally best method for this market. Chronological development checks and a genuinely untouched final period remain a practical starting design here. [12](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)

Report net expectancy, drawdown, profit factor, win/loss sizes, trade count, time in market and results by side/regime—not only win rate. Include higher-cost stress cases and state when there are too few independent trades to draw a conclusion. Do not keep loosening rules until a desired profit or signal count appears.

## Limitations

No cited source tests this exact STAI strategy on its intended OKX instruments under its execution and approval process. The proposed rule values are unvalidated design choices. Academic market/horizon differences, abstract-only access to some papers, and the absence of measured instrument-specific spread/slippage limit generalization.

The current short historical window does not establish robustness across market regimes. Seven warm-up days cannot even provide 99 completed 4h bars: that requires 396 hours before additional stabilization allowance. Longer evaluation windows also need adequate historical funding coverage rather than zero-filled missing rates.

The independent reviewers were AI research assistants, not human traders. This report authorizes no transactions and promises no win rate or profit.

## Recommendations

1. **Approve the corrected 1h/15m baseline for historical testing only**, or revise its explicit rules first. Do not interpret this as trading activation.
2. Implement one shared, versioned strategy definition for scanner and simulator, with tests demonstrating a possible valid long, valid short, invalidation, expiry and no unfinished/future-bar access. Explain every rejected gate in the lab.
3. Preserve comparable runs and distinguish the contradictory legacy baseline from the corrected hypothesis. Do not overwrite old results or manufacture trades.
4. Evaluate costs and out-of-sample behavior before selecting 5m or 4h variants. Never pick the winner by repeatedly reading the same final holdout.
5. Only after the strategy passes research review, connect qualified candidates to advisory Committee review under approved spend caps, followed by deterministic risk sizing and owner approval.

The next useful decision is approval of the test hypothesis—not enabling trading or moving to another development phase.


## Sources

1. [Bitcoin intraday time series momentum](https://onlinelibrary.wiley.com/doi/full/10.1111/fire.12290) — 2022, Tier 1.
2. [Intraday return predictability in the cryptocurrency markets: Momentum, reversal, or both](https://www.sciencedirect.com/science/article/pii/S1062940822000833) — 2022, Tier 1.
3. [AI in Trading](https://fmsb.com/wp-content/uploads/2026/02/FMSB-AI-in-Trading_Final_12.02.26_FINAL.pdf) — 2026-02-12, Tier 2.
4. [Are simple technical trading rules profitable in bitcoin markets?](https://www.sciencedirect.com/science/article/pii/S1059056024003010) — 2024-06, Tier 1.
5. [Intraday price forecasts using candlestick patterns in cryptocurrency markets](https://www.sciencedirect.com/science/article/pii/S1059056026002716) — 2026-06, Tier 1.
6. [Conditional Effectiveness of Volatility-Adaptive Exit Rules in Algorithmic Trading Systems: Evidence from the USD/JPY Market](https://www.mdpi.com/1911-8074/19/8/554) — 2026, Tier 1.
7. [Perpetual funding fee mechanism](https://www.okx.com/en-us/help/perps-funding-fee-mechanism) — Updated 2026-10-28, Tier 1.
8. [OKX V5 API documentation](https://www.okx.com/docs-v5/en/) — Date not stated, Tier 1.
9. [No pain, no gain: You should always incorporate trading costs for a bias-free evaluation of trading rule overperformance](https://www.sciencedirect.com/science/article/abs/pii/S0165176522001720) — 2022, Tier 1.
10. [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) — 2017, Tier 1.
11. [The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) — 2014, Tier 1.
12. [Backtest overfitting in the machine learning era: A comparison of out-of-sample testing methods in a synthetic controlled environment](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110) — 2024-12-03, Tier 1.
