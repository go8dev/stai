---
name: Runtime probe lessons
description: Non-obvious facts learned while testing Freqtrade, TA-Lib and TradingAgents on this Replit runtime before any code was written.
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

**Why:** These took real installs and runs to establish and are not visible in any code.

**How to apply:** Use them when sizing the machine, writing the bot configuration and planning
restart recovery. Re-measure rather than quote them once the real services exist.
