# Upstream register

Everything STAI builds on that STAI did not write: packages, tools, outside services,
template code and the Smart Trader analytics. For each, the version in use, its licence,
what it is used for and how it was integrated. The last sections record exactly what the
analytics port changed and which parts of the starter template remain unused.

Versions and licences were read from the installed packages' own metadata on
18 November 2026. Licence notes are a record, not legal advice.

## How versions are fixed

- **Python.** `pyproject.toml` pins each direct dependency to one exact version, and
  `uv.lock` fixes all 41 packages: 34 run on the published machine and 7 more are for the
  checks only. `uv sync --frozen` installs exactly that set.
- **TypeScript.** `pnpm-lock.yaml` fixes every package. Versions shared by several
  packages are in the catalog in `pnpm-workspace.yaml`. A release must be at least a day
  old before pnpm installs it (`minimumReleaseAge`), except Replit's own packages.
  `pnpm install --frozen-lockfile` installs exactly the locked set.

## Platform and tools

| Tool | Version in the workspace |
| --- | --- |
| Python | 3.12.12 (`pyproject.toml` allows 3.12 only) |
| Node.js | 24.22.1 |
| pnpm | 10.26.1 |
| uv | 0.13.4 |
| PostgreSQL, development server | 16.10 |

The versions on the published machine are the ones Replit provides when the app is
published. They have not been read yet.

## Backend packages

### Declared by STAI

| Package | Version | Licence | Used for |
| --- | --- | --- | --- |
| fastapi | 0.163.1 | MIT | Web framework and the API contract. |
| uvicorn | 0.54.0 | BSD-3-Clause | Server that runs the backend. |
| pydantic | 2.14.3 | MIT | Typed requests, answers and settings. |
| pydantic-settings | 2.16.3 | MIT | Reading settings from environment variables. |
| sqlalchemy | 2.1.9 | MIT | Database access. |
| psycopg, with its binary build | 3.3.9 | LGPL-3.0-only | PostgreSQL driver. |
| alembic | 1.20.1 | MIT | Migrations. |
| httpx | 0.28.1 | BSD-3-Clause | Calls to Replit's sign-in service and to OKX. |
| pyjwt | 2.15.1 | MIT | Checking the identity token. |
| cryptography (required by pyjwt's `crypto` option) | 50.0.2 | Apache-2.0 OR BSD-3-Clause | Signature check of the identity token. |
| pyyaml | 6.0.3 | MIT | Writing the API contract file. |
| tzdata | 2026.6 | Apache-2.0 | Time-zone data for Asia/Manila. |
| numpy | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Analytics only. |
| pandas | 3.1.1 | BSD-3-Clause | Analytics only. |

### Brought in by those

| Licence | Packages |
| --- | --- |
| MIT | annotated-doc 0.0.6, annotated-types 0.8.0, anyio 4.16.0, cffi 2.0.0, h11 0.16.0, mako 1.4.3, pydantic-core 2.50.4, typing-inspection 0.4.5 |
| BSD-3-Clause | click 8.5.1, httpcore 1.0.9, idna 3.18, markupsafe 3.0.4, pycparser 3.0, python-dateutil 4.0.0, python-dotenv 1.2.4, starlette 1.10.0 |
| Apache-2.0 | opentelemetry-api 1.45.2 |
| MPL-2.0 | certifi 2026.10.23 |
| PSF-2.0 | typing-extensions 4.16.0 |

### For the checks only

Not installed on the published machine.

| Package | Version | Licence |
| --- | --- | --- |
| pytest | 9.2.0 | MIT |
| pytest-asyncio | 1.5.0 | Apache-2.0 |
| ruff | 0.17.5 | MIT |
| iniconfig, pluggy | 2.3.1, 1.7.0 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pygments | 2.21.0 | BSD-2-Clause |

### Notes

- **psycopg (LGPL-3.0-only)** and **certifi (MPL-2.0)** are the two packages on the
  published machine whose licences are not of the permissive kind. Both are installed
  unchanged as separate packages and STAI contains no copy of their code.
- **opentelemetry-api** is required by FastAPI 0.163.1. STAI does not import or configure
  it, and the package that would send telemetry anywhere (the SDK) is not in the lock.
- **python-dotenv** arrives with pydantic-settings. STAI reads no `.env` file: the
  settings turn that source off.
- **httpx stays at 0.28.1.** The test client of Starlette 1.10 prefers a newer library,
  `httpx2`, and says so in a deprecation warning, which the test settings silence. 0.28.1
  is the version in the set that was resolved together with Freqtrade and TradingAgents
  (see [Planned, not installed](#planned-not-installed)). Look at this again when that set
  is resolved anew.

## Web app packages

What STAI's own code uses:

| Package | Version | Licence | Used for |
| --- | --- | --- | --- |
| react, react-dom | 19.1.0 | MIT | Interface. |
| vite, @vitejs/plugin-react | 7.3.7, 5.2.0 | MIT | Development server and production build. |
| tailwindcss, @tailwindcss/vite | 4.3.3 | MIT | Styling. |
| tw-animate-css | 1.4.0 | MIT | Animation classes. |
| @tanstack/react-query | 5.104.1 | MIT | Calling the backend through the generated hooks. |
| wouter | 3.13.0 | Unlicense | Routes. |
| lucide-react | 0.545.0 | ISC | Icons. |
| @radix-ui/react-tooltip, @radix-ui/react-toast | 1.3.0, 1.2.24 | MIT | Tooltip and notification components. |
| class-variance-authority | 0.7.1 | Apache-2.0 | Component variants. |
| clsx, tailwind-merge | 2.1.1, 3.7.0 | MIT | Class names. |
| @fontsource-variable/inter | 5.3.0 | OFL-1.1 | Inter, the text typeface. |
| @fontsource/ibm-plex-mono | 5.3.0 | OFL-1.1 | IBM Plex Mono, the typeface for values. |
| zod | 3.25.76 | MIT | Generated validators. |

Tools, not part of the built app:

| Package | Version | Licence | Used for |
| --- | --- | --- | --- |
| typescript | 5.9.3 | Apache-2.0 | Type checks. |
| orval | 8.41.0 | MIT | Generating the client and validators from the API contract. |
| eslint, @eslint/js, typescript-eslint, eslint-plugin-react-hooks, globals | 10.15.0, 10.0.1, 8.72.2, 7.1.1, 17.14.0 | MIT | Lint. |
| prettier | 3.9.10 | MIT | Formatting. |
| @playwright/test | 1.64.1 | Apache-2.0 | Browser test. |
| @replit/vite-plugin-cartographer, -dev-banner, -runtime-error-modal | 0.5.21, 0.1.2, 0.0.6 | None stated in the package | Replit's development helpers. They act on the development server only. |

Both typefaces are bundled with the app. The web app's source names no outside address,
so the browser fetches nothing from a font service or any other third party.

## Code that came from templates or generators

| Path | Origin | State |
| --- | --- | --- |
| `lib/api-client-react/src/generated/`, `lib/api-zod/src/generated/` | Written by Orval from `lib/api-spec/openapi.yaml`. | Never edited by hand. |
| `lib/api-client-react/src/custom-fetch.ts` | The starter's request helper. | Changed for STAI: it fetches the CSRF token and attaches it to requests that change something. |
| `lib/replit-auth-web/` | The browser-side sign-in hook from Replit's sign-in instructions. | Identical to Replit's template except for one statement: logging out sends no return address, because the server decides where a log out ends. |
| `artifacts/api-server/stai/auth/` | STAI's own Python code. It follows the flow of Replit's sign-in instructions, which are written for a Node server. | Written for STAI. |
| `artifacts/stai/src/components/ui/` | The starter's interface components, built on Radix UI. | Kept as supplied. STAI uses four of the 55 files. |
| `artifacts/mockup-sandbox/` | Replit's canvas scaffold. | Not part of STAI. |

## Outside services

| Service | Used for | Credentials |
| --- | --- | --- |
| Replit sign-in, `https://replit.com/oidc` | Proving who is signing in. | The app's Replit ID as a public client with PKCE. No client secret exists. |
| OKX public API, `https://www.okx.com` | One request, `GET /api/v5/public/time`, for the System Status screen. | None. STAI holds no exchange credentials. |
| Replit PostgreSQL | Everything STAI stores. | `DATABASE_URL`, provided by Replit, separately for development and for the published app. |
| Replit hosting | Reserved VM for the backend, static hosting for the web app. | None in the project. |

## Planned, not installed

Nothing in this section is declared, locked or installed in Phase 1. Versions and
licences are the ones recorded in the plan from the runtime checks made before Phase 1.

| Package | Version | Licence | Arrives in |
| --- | --- | --- | --- |
| Freqtrade | 2026.10 | GPL-3.0 | Phase 2 |
| CCXT | 4.5.93 | MIT | Phase 2 |
| TA-Lib | 0.8.3 | To be recorded when installed | Phase 2 |
| TradingAgents | 0.7.1, from its GitHub release tag | Apache-2.0 | Phase 3 |
| LangGraph | 1.2.22 | MIT | Phase 3 |
| OpenAI library | 3.52.0 | To be recorded when installed | Phase 3 |
| Resend, the email service | To be chosen | To be recorded | Phase 4 |
| TradingView Lightweight Charts | To be chosen | To be recorded | With the first chart |

**Version constraints.** `pyproject.toml` lists 142 exact versions under
`constraint-dependencies`. They are the set that was resolved for the Phase 1 backend
together with Freqtrade 2026.10 and TradingAgents 0.7.1. The 41 packages locked today are
among them with identical versions. The other 101 are not installed. The list exists so
that Phases 2 and 3 can add the two engines without moving a version that is already in
use.

**Licence note from the plan.** GPL-3.0 places no obligation on personal use. The
approval gate of Phase 2 plugs into Freqtrade, so the GPL would apply to it if STAI were
ever distributed. Distribution or commercial use needs a legal review first.

## Integration decisions

1. **The backend is Python.** It replaced the starter's Node API server. The starter's
   database package was removed, because SQLAlchemy and Alembic do that work.
2. **Sign-in is written on httpx and PyJWT.** No sign-in library is installed. The flow
   is Replit's OpenID Connect flow with PKCE, and the browser side keeps the route names
   of Replit's instructions.
3. **The backend owns the API contract.** It is exported from the backend to
   `lib/api-spec/openapi.yaml`, and Orval generates the web client and validators from it.
4. **Migrations run in development only.** Replit's Publish step applies structure to the
   published database and carries no triggers, so append-only is enforced in the
   application with a hash chain. See [DATABASE.md](DATABASE.md).
5. **No exchange library in Phase 1.** The OKX check is one public request sent with
   httpx. CCXT and Freqtrade arrive in Phase 2.
6. **Fonts are bundled** through the Fontsource packages instead of a font service.
7. **The logo is used as supplied.** See [Brand files](#brand-files).
8. **The ported analytics are exempt from formatting and most style rules,** so each file
   stays comparable line by line with its source in `stai_handoff/`.

## Analytics port record

Source: `stai_handoff/smart_trader_analytics/`, a snapshot of Smart Trader at commit
`a99c668` (27 October 2026). The files were copied and then changed only as listed here.
The handoff folder itself was not modified.

### Files

Ported to `artifacts/api-server/stai/analytics/` and `artifacts/api-server/tests/analytics/`.

| Source | In STAI | What changed |
| --- | --- | --- |
| `app/utils/numeric.py` | `utils/numeric.py` | Nothing. The file is identical. |
| `app/utils/indicators.py` | `utils/indicators.py` | Import paths. The type name `Kline` became `Candle`. |
| `app/services/btc_regime_service.py` | `services/btc_regime_service.py` | Import paths. One message text: "Binance may be unreachable" became "the market-data provider may be unreachable". |
| `app/services/market_service.py` | `services/market_service.py` | Import paths. `Ticker24h` became `Ticker`. The two Binance calls were replaced (below). Comments that named Binance. |
| `app/services/setup_scoring_service.py` | `services/setup_scoring_service.py` | Import paths. |
| `app/schemas/btc_regime.py`, `market_snapshot.py`, `setup_score.py` | Same names under `schemas/` | Import paths. |
| `app/schemas/scanner.py` | `schemas/scanner.py` | `ScannerCandidate` kept with identical fields. `ScannerResult` left behind. |
| `app/schemas/binance.py` | `schemas/market_data.py` | `Kline` became `Candle` and `Ticker24h` became `Ticker`, fields identical. Left behind: `ConnectivityStatus`, `SymbolInfo`, `FuturesBalance`, `FuturesPosition`, `FuturesOrder`. |
| `app/core/constants.py` | `core/constants.py` | 69 of 89 names kept, each with its original value. 20 left behind (below). |
| `tests/test_numeric.py`, `test_indicators.py`, `test_btc_regime.py`, `test_setup_scoring.py` | Same names under `tests/analytics/` | Import paths, the module paths inside `patch(...)` calls, and the two type names. No test was removed, added or rewritten. |

Added by STAI: the empty package files (`__init__.py`), the interface in
`stai/marketdata/provider.py`, and one rebuilt file, described next.

### One file was rebuilt, not copied

`market_service.py` imports `MarketRegimeResponse` from `app/schemas/market.py`. That file
was not in the handoff. `stai/analytics/schemas/market.py` was written for STAI with the
five fields that `get_btc_regime` fills in: `regime`, `btc_price`, `btc_change_24h`,
`trend` and `updated_at`. The field types were read from how the service fills them. If
Smart Trader's original had further fields or validation, they are not here. Nothing else
in the analytics was written anew.

### The two Binance calls

| Smart Trader | STAI |
| --- | --- |
| `binance_client.get_ticker_24h(symbol)` | `get_market_data_provider().get_ticker(symbol)` |
| `binance_client.get_klines(symbol, timeframe, limit=…)` | `get_market_data_provider().get_candles(symbol, timeframe, limit=…)` |

`MarketDataProvider` can only read a ticker and candles. No provider is registered in
Phase 1, so calling either service function that needs live data fails with a clear
error. The OKX implementation is Phase 2 work, and it has two things to translate, because
the ported code still speaks Binance's dialect: instrument names (`BTCUSDT`) and candle
intervals (`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`).

### Constants left behind

Used only by Smart Trader's order, approval, AI-review, activity-log and scanner code:
`SetupDecision`, `SetupStatus`, `AIDecision`, `AIReviewStatus`, `TradeStatus`,
`CloseReason`, `LogLevel`, `USDT_PAIR_SUFFIX`, `MIN_RSI_PERIOD`, `MAX_RSI_PERIOD`,
`SCANNER_MIN_QUOTE_VOLUME_USDT`, `SCANNER_MIN_CHANGE_PCT`, `SCANNER_MAX_CANDIDATES`,
`SCANNER_SYMBOL_BLACKLIST_FRAGMENTS`, `AI_MIN_SCORE_FOR_REVIEW`, `AI_TEMPERATURE`,
`AI_MAX_TOKENS`, `AI_CONFIDENCE_MIN`, `AI_CONFIDENCE_MAX`, `AI_MAX_SL_WIDENING_FRACTION`.

### How the port was checked

- **Same logic.** Each ported module was compared with its source as parsed code, with
  imports and comments set aside and the two type names mapped. Three statements differ
  in all: the two calls above and the one message text. The 69 constants and the three
  kept data shapes compare as identical.
- **Same tests.** The 191 tests pass in STAI on Python 3.12.12 with pandas 3.1.1, numpy
  2.5.5 and pydantic 2.14.3: 22 numeric, 52 indicators, 44 BTC regime, 73 setup scoring.
  These are the counts the handoff reports, on the same library versions.

### The six steps of the handoff's port list

| # | Step | State |
| --- | --- | --- |
| 1 | Replace the two Binance calls. | Done through the interface. The OKX provider behind it is Phase 2. |
| 2 | Rename the Binance data shapes. | Done. Function and variable names such as `klines_to_df` were left as they are. |
| 3 | Use STAI's logging and settings. | Logging done: STAI provides a logger of the same name with the methods the ported code calls. None of the files imported Smart Trader's settings. |
| 4 | Keep only the exports STAI uses. | Done, as listed above. |
| 5 | Floats are for indicators only. | Kept in mind, not yet enforced by anything: the decimal ledger is Phase 2. |
| 6 | Review the stop and target rules for BTC, ETH and SOL on OKX. | Open. To be done before the pilot. |

## Brand files

Source: `stai_handoff/brand/`, two PNG files of 1013 by 1010 pixels, read-only.

| File in `artifacts/stai/public/` | What it is |
| --- | --- |
| `brand/stai-logo-on-dark-320.webp`, `brand/stai-logo-on-dark-640.webp` | The supplied white-text logo, resized to 320 and 640 pixels wide and compressed, with its transparency kept. Nothing was redrawn: compared pixel by pixel with the supplied file at the same size, each copy differs by under 0.3%. |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png` | The simplified S, drawn for STAI. It is used only as the browser-tab icon and the small app icons, because the supplied mark blurs below 32 pixels. This is item 8 of the plan. |

The light-background logo is not used yet. It is for emails and printed reports. The
interface keeps the specification's accent colour and the logo keeps its own teal. The
logo stays provisional, as the specification says.

## Starter parts that STAI does not use

They came with the project template and were left in place. None of them is in the built
web app or loaded by the backend.

| What | Where |
| --- | --- |
| 51 interface components, and the packages only they need | `artifacts/stai/src/components/ui/`, `artifacts/stai/package.json` |
| `@replit/connectors-sdk` 0.7.0, which nothing imports | Root `package.json` |
| A sample script | `scripts/src/hello.ts` |
| A workspace pattern for a folder that does not exist | `lib/integrations/*` in `pnpm-workspace.yaml` |
| A catalog entry for a package nothing uses | `drizzle-orm` in `pnpm-workspace.yaml` |
| The secret `SESSION_SECRET` | Replit Secrets. STAI's sessions do not use it. |
| Replit's canvas scaffold | `artifacts/mockup-sandbox/` |

## Keeping this register current

Update it in the same change that adds a package, moves a version or brings in outside
code. Read versions and licences from what is installed, not from memory:

```bash
uv export --frozen --no-dev --no-hashes --no-emit-project   # packages on the published machine
uv tree --frozen --invert --package <name>                  # what requires a package
pnpm why <name>                                             # the same for TypeScript
```
