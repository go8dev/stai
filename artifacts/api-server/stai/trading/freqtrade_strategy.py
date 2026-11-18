"""A Freqtrade strategy that never invents entry signals.

No approval endpoint exists until Phase 4. This Phase 2 strategy therefore keeps
every entry signal at zero and refuses every entry, while still allowing the two
private dry-run bots to connect to public OKX data and report health.
"""

from __future__ import annotations

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class StaiGateStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 10}
    stoploss = -0.05
    startup_candle_count = 100
    order_types = {
        "entry": "market",
        "exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def confirm_trade_entry(
        self,
        pair,
        order_type,
        amount,
        rate,
        time_in_force,
        current_time,
        entry_tag,
        side,
        **kwargs,
    ) -> bool:
        # Intentionally fail closed until Phase 4 connects the owner-approval flow.
        return False

    def leverage(
        self,
        pair,
        current_time,
        current_rate,
        proposed_leverage,
        max_leverage,
        entry_tag,
        side,
        **kwargs,
    ) -> float:
        return min(2.0, max_leverage)


class StaiFuturesGateStrategy(StaiGateStrategy):
    """The same closed gate, with short support only in the futures engine."""

    can_short = True
