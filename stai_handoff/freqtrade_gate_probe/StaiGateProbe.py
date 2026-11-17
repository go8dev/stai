"""Feasibility probe only: a Freqtrade strategy that never signals an entry on its own
and lets an entry through only when it matches an approved proposal."""
import json
from datetime import datetime, timezone
from pathlib import Path

from pandas import DataFrame

from freqtrade.strategy import IStrategy

APPROVALS = Path("/tmp/ftprobe/approvals.json")
GATE_LOG = Path("/tmp/ftprobe/gate.log")


class StaiGateProbe(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = True
    minimal_roi = {"0": 10}
    stoploss = -0.10
    startup_candle_count = 0
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

    def leverage(self, pair, current_time, current_rate, proposed_leverage, max_leverage,
                 entry_tag, side, **kwargs) -> float:
        return min(2.0, max_leverage)

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        try:
            approved = json.loads(APPROVALS.read_text())
        except Exception:
            approved = {}
        a = approved.get(entry_tag or "")
        notional = amount * rate
        reason = "approved"
        if a is None:
            reason = "no approval for this proposal id"
        elif a["pair"] != pair or a["side"] != side:
            reason = "approval is for different parameters"
        elif notional > a["max_notional"] * 1.001:
            reason = "notional above approved amount"
        ok = reason == "approved"
        with GATE_LOG.open("a") as fh:
            fh.write(json.dumps({
                "utc": datetime.now(timezone.utc).strftime("%H:%M:%S"), "proposal": entry_tag,
                "pair": pair, "side": side, "notional": round(notional, 2),
                "decision": "ALLOW" if ok else "DENY", "reason": reason}) + "\n")
        return ok
