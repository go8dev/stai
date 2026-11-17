"""Rule-based market analytics carried over from Smart Trader.

Ported by copying from `stai_handoff/smart_trader_analytics` (Smart Trader commit a99c668),
not rewritten: indicators, BTC regime, market snapshot and setup scoring. What changed in
the port is listed in docs/UPSTREAM_REGISTER.md. In short: imports, exchange-neutral
names for the candle and ticker shapes, STAI's logger, and a market-data interface in
place of the two Binance calls.

These modules work in floats, which is fine for indicators. Quantities and money never
pass through them; those belong to the decimal ledger that arrives in Phase 2.
"""
