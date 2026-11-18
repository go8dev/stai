---
name: Runtime probe lessons
description: Non-obvious runtime behavior of Freqtrade, SQLite recovery, TA-Lib, TradingAgents and public OKX data.
---

- TradingAgents is not on the Python package index. Install it from its GitHub release tag
  (`git+https://github.com/TauricResearch/TradingAgents@v0.7.1`). It resolves together with
  Freqtrade 2026.10 in one environment.
- TA-Lib installs as a prebuilt wheel here; no system library or compiler step was needed.
- Throwaway experiments belong outside the project (a `--target` install under `/tmp`), so the
  project gains no dependency files before the owner approves a phase.
- A futures dry-run bot needs about 2.5 minutes on one core before its API is ready, almost all
  of it loading leverage tiers for every market. That cache lives under the bot's `user_data`
  folder, which a published VM loses on restart. Restricting market loading to spot and swap
  (`exchange.ccxt_config.options.fetchMarkets.types`) is what keeps it from being slower.
- Dry-run fee rates come from the exchange library's built-in table, not from an OKX account,
  and differ between spot and perpetuals. Treat them as defaults, keep them configurable.
- Two idle bots (spot + futures, three pairs each) used roughly 0.8 GB together. Memory for the
  API, worker and an AI run on top was not measured.
- This workspace is hosted in Asia, so OKX reachability from a US deployment cannot be tested
  from here; it can only be checked on a published machine.
- Freqtrade validates required credential fields inside API/Telegram blocks even when
  `enabled` is false. Omit unused blocks entirely; validate against the installed schema
  before a network startup. **Why:** a disabled block still prevented both bots starting.
- OKX's full spot instrument list can exceed a defensive 1 MB response cap.
  Query individual instrument IDs rather than raising the cap.
  **Why:** a successful public response otherwise looked like a scanner outage.
- SQLite's backup-to-memory plus serialize retains WAL header flags from Freqtrade.
  Normalize an isolated on-disk backup to DELETE journaling before packaging it.
  **Why:** deserializing the WAL-marked bytes fails with "unable to open database file"
  despite the backup containing all pages. Test against WAL, not only default SQLite mode.

**Why:** These took real installs and runs to establish and are not visible in any code.

**How to apply:** Use them when sizing the machine, writing the bot configuration and planning
restart recovery. Re-measure rather than quote them once the real services exist.

Dependency additions can change Starlette's preferred HTTP client and its logging behavior.
**Why:** Adding TradingAgents pulled in httpx2; Starlette began using it, and its normal
request logger emitted sign-in query strings that the older client's log suppression did not cover.
**How to apply:** Re-run token/query redaction tests after HTTP-client dependency changes.
Suppress all installed transport request loggers, not just the client STAI imports directly.

TradingAgents' model catalog may reject a dated model ID as unknown even when the provider accepts it.
**Why:** The pinned release recognizes model families but warned for the exact snapshot
used by the real benchmark. A warning is not a failed provider call.
**How to apply:** Verify the provider's actual model/usage and pricing; do not silently
substitute a different model to suppress the catalog warning or repeat a paid run.
