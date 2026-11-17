# Smart Trader analytics carried into STAI

Source: Smart Trader project, commit `a99c668` (27 October 2026).

This folder is a source snapshot for porting. It is not a runnable package here, because
the data-access modules it imports were left behind on purpose (see the last section).

## Verified

Run with Smart Trader's full module set present, on Python 3.13.11 with pandas 3.1.1,
numpy 2.5.5 and pydantic 2.14.3. Smart Trader itself runs on Python 3.11.

| Test file | Result |
|---|---|
| `tests/test_numeric.py` | 22 passed |
| `tests/test_indicators.py` | 52 passed |
| `tests/test_btc_regime.py` | 44 passed |
| `tests/test_setup_scoring.py` | 73 passed |
| Total | 191 passed |

## What is here

- `app/utils/indicators.py`: EMA 7/25/99, RSI 14, MACD, volume ratio, candle shape, ATR, risk/reward.
- `app/utils/numeric.py`: safe conversions and rounding to exchange steps.
- `app/services/btc_regime_service.py`: BTC regime from 1-hour (weight 0.6) and 15-minute (weight 0.4) snapshots.
- `app/services/setup_scoring_service.py`: 0 to 100 rule score in 8 components, plus stop and target derivation.
- `app/services/market_service.py`: builds a market snapshot from candles.
- `app/core/constants.py`: enums and thresholds.
- `app/schemas/`: data shapes used by the modules above.
- `tests/`: the four test files listed above.

## Port work

1. Replace the two Binance calls in `market_service.py` (`get_klines`, `get_ticker_24h`)
   with OKX candles and ticker from STAI's market-data service.
2. Rename the Binance data shapes (`Kline`, `Ticker24h`) to exchange-neutral names.
3. Replace the `StructuredLogger` and settings imports with STAI's logging and settings.
4. Keep only the schema exports STAI uses.
5. These modules use floats. That is fine for indicators. Quantities and money go through
   STAI's decimal ledger.
6. The stop and target rules (stop at EMA 99 plus or minus 1.5%, targets at 1.5%, 3.5%
   and 7%) were written for Smart Trader's Binance futures scanner. Review them for BTC,
   ETH and SOL on OKX before the pilot.

## Left behind on purpose

- `app/integrations/binance_client.py` and `app/core/config.py`: exchange API key fields and signed requests.
- The trading-enabled flag and the execution and trade services: order paths.
- Telegram client, Express mock API, React interface.
- `app/services/scanner_service.py`: scans all Binance futures by 24-hour volume and price
  move. STAI watches three fixed instruments.
