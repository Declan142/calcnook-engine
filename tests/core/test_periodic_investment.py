"""Tests for periodic_investment (SIP / DCA with optional step-up)."""

import pytest

from calcnook.core import periodic_investment


def test_basic_sip_5k_12pct_10y():
    # Standard reference: 5000/mo @ 12% for 10 years (120 months)
    # r = 0.01, n = 120
    # FV = 5000 * ((1.01^120 - 1) / 0.01) * 1.01
    import math
    r = 0.01
    n = 120
    expected_fv = 5000 * ((1 + r) ** n - 1) / r * (1 + r)
    result = periodic_investment.calculate(5000, 0.12, 10)
    assert pytest.approx(result.future_value, rel=1e-4) == expected_fv


def test_total_invested_no_step_up():
    result = periodic_investment.calculate(5000, 0.12, 10)
    assert result.total_invested == pytest.approx(5000 * 120, rel=1e-6)


def test_wealth_gained_equals_fv_minus_invested():
    result = periodic_investment.calculate(5000, 0.12, 10)
    assert result.wealth_gained == pytest.approx(
        result.future_value - result.total_invested, rel=1e-6
    )


def test_zero_amount():
    result = periodic_investment.calculate(0, 0.12, 10)
    assert result.future_value == 0.0
    assert result.total_invested == 0.0
    assert result.wealth_gained == 0.0


def test_zero_years():
    result = periodic_investment.calculate(5000, 0.12, 0)
    assert result.future_value == 0.0
    assert result.total_invested == 0.0


def test_zero_rate():
    # Zero return: FV = P * n (no growth)
    result = periodic_investment.calculate(1000, 0.0, 5)
    assert result.future_value == pytest.approx(1000 * 60, rel=1e-6)
    assert result.total_invested == pytest.approx(1000 * 60, rel=1e-6)


def test_step_up_increases_future_value():
    no_step = periodic_investment.calculate(5000, 0.12, 10, step_up_percent=0.0)
    with_step = periodic_investment.calculate(5000, 0.12, 10, step_up_percent=10.0)
    assert with_step.future_value > no_step.future_value
    assert with_step.total_invested > no_step.total_invested


def test_step_up_total_invested_grows():
    # With 10% step-up, year 2 contribution = 5000 * 1.1 = 5500/mo, etc.
    result = periodic_investment.calculate(5000, 0.12, 2, step_up_percent=10.0)
    # Year 1: 5000 * 12 = 60000; Year 2: 5500 * 12 = 66000; total = 126000
    assert result.total_invested == pytest.approx(126000, rel=1e-4)


def test_negative_amount_rejected():
    with pytest.raises(ValueError, match="monthly_amount"):
        periodic_investment.calculate(-1000, 0.12, 10)


def test_negative_years_rejected():
    with pytest.raises(ValueError, match="years"):
        periodic_investment.calculate(5000, 0.12, -1)


def test_negative_step_up_rejected():
    with pytest.raises(ValueError, match="step_up_percent"):
        periodic_investment.calculate(5000, 0.12, 10, step_up_percent=-5.0)


def test_to_dict_keys():
    result = periodic_investment.calculate(5000, 0.12, 10)
    d = result.to_dict()
    for key in ("monthly_amount", "annual_return", "years", "step_up_percent",
                "total_invested", "future_value", "wealth_gained"):
        assert key in d


def test_to_dict_rounding():
    result = periodic_investment.calculate(5000, 0.12, 10)
    d = result.to_dict()
    # Values should be rounded to 2dp
    assert d["future_value"] == round(result.future_value, 2)
    assert d["total_invested"] == round(result.total_invested, 2)
