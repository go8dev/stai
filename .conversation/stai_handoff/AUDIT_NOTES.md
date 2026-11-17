# STAI pre-build audit notes

Date: 17 November 2026 (UTC). Working notes from the review of the STAI master prompt v1.0.
"Verified" means observed directly in the cloned repositories or on a live run on this date.
Open items are listed at the end. Nothing here is legal advice.

## Upstream versions and licenses

| Component | Version checked | License | Role in STAI |
|---|---|---|---|
| Freqtrade | 2026.10 (stable) | GPL-3.0-only | Paper execution engine, run unmodified as a separate process |
| FreqUI | not installed | GPL-3.0 | Not needed, STAI has its own UI |
| TradingAgents | 0.7.1 (2026-10-27) | Apache-2.0 | Committee graph, adapted for crypto |
| LangGraph | as required by TradingAgents | MIT | Agent orchestration |
| CCXT | 4.5.93 (pulled in by Freqtrade) | MIT | Exchange access |
| ai-hedge-fund | reference only | MIT | Architecture reference |
| Hummingbot | reference only | Apache-2.0 | Architecture reference |

Freqtrade needs Python 3.12 or newer. Installed cleanly on Python 3.13.11 with TA-Lib 0.8.3.
The install is about 590 MB on disk.

## Freqtrade (verified)

- OKX support covers spot and futures; futures are isolated margin only.
- One `trading_mode` per bot. STAI needs two dry-run bots (spot and futures), each with its
  own database or schema and its own dry-run wallet.
- Money is stored as floats (41 Float columns, 0 Numeric). Freqtrade cannot be the book of record.
- Entries come from strategy signals or `POST /api/v1/forceenter` (needs `force_entry_enable`).
  The payload has pair, side, price, order type, stake amount, entry tag and leverage.
  It has no stop-loss or take-profit fields and takes a stake, not a quantity.
- `confirm_trade_entry` is called for every initial entry, including forced ones.
  It is not called for position adjustments. With `position_adjustment_enable` off, a second
  entry on a pair that already has an open trade is refused by Freqtrade itself.
- Pause (`/api/v1/pause`, alias `/api/v1/stopentry`) refuses new entries, including forced
  ones ("trader is not running"), and keeps handling exits.
- Dry-run market orders fill from the live order book, instantly and in full (order filled
  1 ms after creation). No latency and no partial fills are simulated. Funding fees are
  calculated. Liquidation price is estimated; no liquidation fee.
- The stored `fee_open_cost` is fee rate times stake (margin), so with leverage it understates
  the entry fee (`persistence/trade_model.py` line 1338 in 2026.10). The profit calculation
  itself charges the fee on notional on both sides. STAI must compute fees from fills.
- OKX candle downloads return 100 candles per call; mark-price candles go back about 3 months.
- Start-up took about 2 minutes on 1 vCPU, mostly loading leverage tiers for 528 markets
  (cached under `user_data` afterwards). Idle memory was about 435 MB for one futures bot
  with three pairs. Market loading was limited to spot and swap through
  `exchange.ccxt_config.options.fetchMarkets.types`.

## Approval gate probe (verified, live OKX perpetuals, no API keys)

Files: `freqtrade_gate_probe/` (strategy, example config without secrets, gate decisions).
The strategy never signals an entry and allows an entry only when the entry tag matches an
approved proposal with the same pair, side and a notional at or below the approved amount.

| Test | Result |
|---|---|
| Entry with no approval on file | Refused |
| Approval exists for a different pair and side | Refused |
| Approved proposal, size doubled | Refused |
| Exactly the approved trade (ETH short, 100 USDT notional, 2x) | Filled |
| ETH long, order book timestamped before and after | Filled at 1806.61, best ask 1806.61 |
| SOL short, order book timestamped before and after | Filled at 72.94, best bid 72.94 |
| Second approved entry on a pair with an open position | Refused by Freqtrade |
| Approved entry while Freqtrade is paused | Refused by Freqtrade |
| Closing all positions while paused | Worked |
| Entries started by the bot itself | None |

- Fee charged: 0.05% of notional per side on perpetuals.
- Three round trips of about 100 USDT notional cost 0.108, 0.096 and 0.114 USDT.
- Wallet went from 400.0000 to 399.68333561, equal to the sum of the three trade results.
- Liquidation price at 2x isolated was about 47% away from entry (ETH long 952.35 from 1806.61).

Still to build on top of this probe: binding of leverage, stop, target and expiry to the
approval; single use of each approval; price-drift check at execution time.

## OKX (verified from this sandbox, which is located in Asia)

- Public REST works without keys: tickers, order books, instruments, funding rates.
- Minimum sizes: spot BTC 0.00001, ETH 0.0001, SOL 0.01. Perpetual contract values are
  0.01 BTC, 0.1 ETH and 1 SOL with a minimum of 0.01 contracts, so minimum notionals were
  about 6.4, 1.8 and 0.7 USDT. All fit a 200 USDT position cap and a 5 USDT planned risk.

## TradingAgents (verified from the repository)

- Built for equities on daily data from Yahoo. Crypto appears only as Yahoo tickers such as BTC-USD.
- No OKX data, no funding, open interest or other derivatives inputs.
- Roles: market, social, news and fundamentals analysts, bull and bear researchers with a
  research manager, trader, three risk debaters, portfolio manager. No quantitative or
  derivatives role.
- Output is a 5-tier rating with free-text sizing. At least 12 model calls per run.
- Memory and checkpoints are kept in files or SQLite.

## Replit hosting (from Replit documentation)

- Always-on background workers need a Reserved VM deployment.
- A published app's filesystem is not persistent; state must live in the database.
- Development and production databases are separate.
- Deployment region is selectable; the default is the United States.
- Replit AI Integrations bill model usage to the Replit account at provider rates.

## Existing Smart Trader project

- Binance futures assistant: React and Vite frontend, Express mock API, FastAPI on Python 3.11,
  SQLite, autoscale deployment, Telegram alerts. Commits on 27 October began adding OKX data.
- Contains exchange API key fields, a `trading_enabled` flag and a stubbed real-order path.
  These conflict with section 12 of the STAI prompt.
- Its notes claim 319 tests. The 191 analytics tests were run later (see "Smart Trader
  analytics reuse" below). The others were not run.

## Logo file

- 1536 x 1024 PNG, RGB, no transparency. Background is #040B1C; the prompt's app background is #0B1220.
- Logo teal is #00D6C8; the prompt's accent is #25C6B0.
- Background removal by colour keying works. The S mark is clear at 64 px and above and blurs at 16 to 32 px.

## Owner decisions (17 November 2026)

| Question | Decision |
|---|---|
| Where to build | New project, reusing only Smart Trader's analytics |
| Trading rhythm | Intraday, 15 to 60 minutes |
| AI model billing | Owner's own API key |
| Alerts | Email |
| Logo | Second file supplied (transparent PNG) |

## Proposed consequences, for approval in the Phase 1 plan

- Timeframes: 1-hour trend with 15-minute entry timing. The reused analytics already work this way.
- Rule scoring runs every 15 minutes at no model cost. The AI committee runs only on setups
  above a score threshold, with a daily cap on runs and on spend. Cost and duration per run
  are measured before the caps are set.
- Proposals are valid for 60 minutes by default (configurable), entered as a limit order at
  the proposed price, and re-validated against the live price at approval. A changed price
  or an expired proposal needs a new approval.
- Sizing arithmetic: 0.5% risk is 5 USDT and the 20% cap is 200 USDT. They meet at a 2.5%
  stop distance. With a tighter stop the cap sets the size and the risk is below 5 USDT.
- Email: one message per proposal linking to the approval page, a daily summary, and risk and
  outage alerts. Approval happens only in the app after login. A setting defines the hours in
  which proposals are sent; setups outside those hours are tracked but not sent.
- AI provider assumed to be OpenAI, as in Smart Trader. The key is stored in project Secrets.
- Email provider: Resend or SendGrid, both already authorized on the owner's Replit account.

## Smart Trader analytics reuse (verified)

- Source commit `a99c668` (27 October 2026). Files and port steps: `smart_trader_analytics/README.md`.
- 191 tests passed on Python 3.13.11 with pandas 3.1.1, numpy 2.5.5 and pydantic 2.14.3:
  numeric 22, indicators 52, BTC regime 44, setup scoring 73.
- Carried: indicators, numeric helpers, BTC regime classifier, setup scoring, snapshot builder,
  constants, data shapes and their tests.
- Left behind: Binance client and exchange key settings, trading-enabled flag, execution and
  trade services, Telegram, mock API, interface, and the Binance-wide scanner.

## Second logo file

- PNG, 1536 x 1024, with transparency. It contains no vector data.
- The wordmark, tagline and ring are dark navy (#01152A): contrast 1.02:1 on the app
  background (#0B1220) and 18.4:1 on white. It is the light-background version.
- Brand files prepared in `brand/`:
  - `stai_logo_dark_background.png`: the second file with only the navy parts switched to white.
  - `stai_logo_light_background.png`: the second file as supplied, with 35 faint stray specks removed.
  - A third file, the first logo with its background removed, was not carried into this
    folder. The owner sent the second file after being asked for a vector version, so the
    second file is treated as the current logo.
- The browser-tab icon still needs a simplified S below 32 px.

## Not yet verified

- OKX public API reachability from a US-hosted deployment.
- Dry-run fee rates in spot mode.
- Model cost and duration per committee run on intraday data.
- Machine size needed for two bots, the API and an AI run together.
- Email delivery from the deployed app.
