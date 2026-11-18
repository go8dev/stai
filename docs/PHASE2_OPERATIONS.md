# Phase 2 operation

## Safety boundary

Only public OKX GET requests are used by STAI. The two unmodified Freqtrade 2026.10
processes are forced into dry-run, have no exchange credentials, inherit a restricted
environment, expose no API and run no Telegram service. Their strategy produces no
entry signals and `confirm_trade_entry` always returns false. No permit-creation or
order-submission endpoint exists in Phase 2. Phase 4 must connect the tested permit
validator to the owner's exact-trade approval workflow before any entry is possible.

The validator checks the approved instrument, direction, exact notional, price band,
stop, target, leverage, expiry and single use, as well as current market data,
reconciliation, ledger integrity and the portfolio's three-position limit.
Spot is long-only at 1x; futures are isolated at up to 2x. This is not yet Phase 4's
complete risk engine, daily-loss control or emergency halt interface.

## Data and accounting

The Scanner covers BTC/ETH/SOL spot and USDT swaps, using 1h and 15m candles,
tickers, five-level books, instrument rules and swap funding rates. Ticker/book
timestamps older than 60 seconds, future timestamps and old candles cannot produce
a fresh screening result. Only closed candles feed the copied analytics.
Swap book sizes are converted from contracts into base units.

The real persistent virtual fund is initialized once, not a UI mock: 600 USDT spot
and 400 USDT futures. PostgreSQL Numeric/Decimal values, not binary floats, carry
money and quantities. Indicator calculations retain the upstream float analytics.
Portfolio reports cash, reserved futures collateral, available balance, mark exposure,
fees, signed funding and realized/unrealized P&L. A stale mark is labelled, not hidden.

FeeSchedule is configurable in the accounting service. Defaults are spot maker/taker
0.10%/0.15% and futures maker/taker 0.02%/0.05%, measured from CCXT's public defaults,
not the owner's OKX account tier. Fees apply to filled notional, not leveraged margin.
The book-walk estimator refuses more than 10% of displayed depth and never improves
the engine's execution price. Raw and adjusted fill prices, spread and slippage stay
in the immutable fill record and hashed ledger evidence.

Completed engine orders can only be imported with a matching consumed permit and
timely recorded order-book evidence. Unknown or unapproved orders block reconciliation.
Retries use stable fill and funding identifiers and cannot double-count. Snapshot
imports and their saved engine database occur in the same PostgreSQL transaction.
With the entry strategy closed, normal Phase 2 operation has no fills or positions.
Actual approval-to-fill operation is not exercised until Phase 4.

## Worker and restart recovery

`artifacts/api-server: Paper Worker` serves only a private health port on 8099.
Its service declares no public paths. A PostgreSQL advisory lock prevents two workers.
It scans every 15 minutes and checks the engine snapshots about every 5 seconds.
Reconciliation compares each market's engine position IDs, quantities, raw entry
averages, direction and leverage to ledger-backed positions, and verifies the ledger.
An absent, stopped or inconsistent engine is not declared reconciled.

Each bot uses a private temporary SQLite database. Consistent compressed snapshots
and SHA-256 checksums are stored in PostgreSQL, as explicitly required by the approved
architecture because published files are ephemeral. They contain no exchange keys.
Startup verifies checksum and SQLite integrity before restoring; shutdown stops both
bots and saves final snapshots. A kill can lose up to one polling interval of
unobserved engine state; the ledger is never fabricated to hide a mismatch.

The production command intentionally omits `--enable-paper-bots`. Before changing it:

1. Owner completes Phase 1 production restart check 7.
2. Owner reviews Phase 2 and the production schema diff in Publishing.
3. Owner authorizes continuous paper-worker operation and republishes with no positions open.
4. Confirm both private bots run, reconcile and survive a production restart.

Do not change production, publish, change VM size or start the pilot automatically.

## Integrity limitation

The owner chose database-only hash chains. Full verification detects changed content,
broken predecessor links and gaps, but cannot prove that the newest rows were not
deleted or that a privileged database user did not rebuild the entire chain.
Application append-only guards prevent accidental writes, not privileged DB tampering.
There is no external anchor and no claim of tamper-proof storage.

## Workspace verification

On 18 November 2026:

- `pnpm run check` passed: lint, formatting, TypeScript checks, API contract and
  1,235 Python tests (32 focused Phase 2 cases).
- Production web build passed with the artifact's required PORT/BASE_PATH inputs.
- Public OKX returned fresh data for all six supported market/symbol combinations.
- Both private workspace bots reached RUNNING, reconciled clear with zero positions,
  kept the entry gate closed and saved checksummed recovery snapshots.
- `pnpm run test:browser` passed 60 desktop/phone cases. Signed-out checks use the
  real backend; signed-in Scanner/Portfolio checks use clearly synthetic contract
  fixtures, not the real owner's session or production data.
- The signed-in production UI and a production restart were not tested by the agent.
  Owner screenshots establish Phase 1's live sign-in/status/audit result only.
