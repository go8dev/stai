"""
Tests for app/utils/numeric.py — safe_float, safe_int, rounding helpers.
"""
import pytest
from stai.analytics.utils.numeric import (
    safe_float,
    safe_int,
    round_to_precision,
    round_to_step,
    pct_change,
)


# ── safe_float ─────────────────────────────────────────────────────────────────

class TestSafeFloat:
    def test_converts_string(self):
        assert safe_float("3.14") == 3.14

    def test_converts_int(self):
        assert safe_float(5) == 5.0

    def test_converts_float(self):
        assert safe_float(2.718) == 2.718

    def test_none_returns_default(self):
        assert safe_float(None) == 0.0

    def test_none_custom_default(self):
        assert safe_float(None, default=-1.0) == -1.0

    def test_empty_string_returns_default(self):
        assert safe_float("") == 0.0

    def test_invalid_string_returns_default(self):
        assert safe_float("abc") == 0.0

    def test_nan_returns_default(self):
        import math
        assert safe_float(float("nan")) == 0.0

    def test_inf_returns_default(self):
        assert safe_float(float("inf")) == 0.0


# ── safe_int ───────────────────────────────────────────────────────────────────

class TestSafeInt:
    def test_converts_string(self):
        assert safe_int("42") == 42

    def test_converts_float_string(self):
        assert safe_int("3.9") == 3

    def test_none_returns_default(self):
        assert safe_int(None) == 0

    def test_invalid_returns_default(self):
        assert safe_int("xyz") == 0


# ── round_to_precision ─────────────────────────────────────────────────────────

class TestRoundToPrecision:
    def test_two_decimals(self):
        assert round_to_precision(64321.675, 2) == 64321.68

    def test_zero_decimals(self):
        assert round_to_precision(99.9, 0) == 100.0

    def test_negative_precision_passthrough(self):
        # negative precision is a no-op
        assert round_to_precision(1.23456, -1) == 1.23456


# ── round_to_step ──────────────────────────────────────────────────────────────

class TestRoundToStep:
    def test_step_001(self):
        result = round_to_step(1.2349, 0.001)
        assert result == pytest.approx(1.234, rel=1e-6)

    def test_step_10(self):
        result = round_to_step(64325.0, 10.0)
        assert result == pytest.approx(64320.0, rel=1e-6)

    def test_zero_step_passthrough(self):
        assert round_to_step(1.5, 0.0) == 1.5


# ── pct_change ─────────────────────────────────────────────────────────────────

class TestPctChange:
    def test_positive_change(self):
        assert pct_change(100.0, 110.0) == pytest.approx(10.0)

    def test_negative_change(self):
        assert pct_change(100.0, 90.0) == pytest.approx(-10.0)

    def test_zero_old_returns_zero(self):
        assert pct_change(0.0, 50.0) == 0.0
