"""
Safe numeric helpers for financial data.

Design intent:
  - All functions accept raw values (str, float, None) and return clean floats.
  - Structure is ready for Decimal drop-in: replace float() with Decimal() here
    and callers need no changes.
  - Never raise on bad input — log and return the default instead.
"""
import math
from typing import Union

RawNumber = Union[str, float, int, None]


def safe_float(value: RawNumber, default: float = 0.0) -> float:
    """
    Safely convert any raw value to float.
    Returns `default` on None, empty string, or parse failure.
    """
    if value is None:
        return default
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_int(value: RawNumber, default: int = 0) -> int:
    """Safely convert any raw value to int. Returns `default` on failure."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def round_to_precision(value: float, precision: int) -> float:
    """
    Round a float to `precision` decimal places.
    Used to match exchange price/quantity precision rules.

    Example:
        round_to_precision(64321.675, 2) → 64321.68
    """
    if precision < 0:
        return value
    return round(value, precision)


def round_to_step(value: float, step: float) -> float:
    """
    Quantize `value` to the nearest multiple of `step`.
    Used to match exchange LOT_SIZE / TICK_SIZE filters.

    Example:
        round_to_step(1.2345, 0.001) → 1.234
    """
    if step <= 0:
        return value
    precision = max(0, -int(math.floor(math.log10(step))))
    return round(math.floor(value / step) * step, precision)


def pct_change(old: float, new: float) -> float:
    """Calculate percentage change from old to new. Returns 0.0 if old is 0."""
    if old == 0:
        return 0.0
    return round((new - old) / abs(old) * 100, 4)
