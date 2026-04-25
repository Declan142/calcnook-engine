"""Tests for hajj_savings (Hajj savings planner)."""

import pytest

from calcnook.core.islamic import hajj_savings


# --- Core calculation ---

def test_monthly_contribution_10k_5y_6pct_zero_savings():
    r = hajj_savings.calculate(10_000, 5, current_savings=0, expected_annual_return=0.06)
    # Sanity: contribution should be positive and roughly ~$143-145/mo
    assert r.monthly_contribution_needed > 0
    assert round(r.monthly_contribution_needed, 2) == pytest.approx(143.33, abs=1.0)


def test_total_contribution_equals_monthly_times_months():
    r = hajj_savings.calculate(10_000, 5, current_savings=0, expected_annual_return=0.06)
    assert pytest.approx(r.total_contribution, abs=0.01) == r.monthly_contribution_needed * 60


def test_with_existing_savings_reduces_contribution():
    r_no_savings = hajj_savings.calculate(10_000, 5, current_savings=0, expected_annual_return=0.06)
    r_with_savings = hajj_savings.calculate(10_000, 5, current_savings=8_000, expected_annual_return=0.06)
    assert r_with_savings.monthly_contribution_needed < r_no_savings.monthly_contribution_needed


def test_already_met_zero_contribution():
    # 8000 savings, 1y, 6% → FV = ~8486 > 8000 target
    r = hajj_savings.calculate(8_000, 1, current_savings=8_000, expected_annual_return=0.06)
    assert r.target_met_at_zero_contribution is True
    assert r.monthly_contribution_needed == 0.0
    assert r.total_contribution == 0.0


def test_zero_return_fallback():
    # Without any return, simple division: 12000 / (5*12) = 200/mo
    r = hajj_savings.calculate(12_000, 5, current_savings=0, expected_annual_return=0.0)
    assert round(r.monthly_contribution_needed, 2) == 200.00


def test_expected_growth_positive_with_return():
    r = hajj_savings.calculate(10_000, 5, current_savings=0, expected_annual_return=0.06)
    assert r.expected_growth > 0


def test_expected_growth_zero_at_zero_return():
    r = hajj_savings.calculate(10_000, 5, current_savings=0, expected_annual_return=0.0)
    assert pytest.approx(r.expected_growth, abs=0.01) == 0.0


def test_to_dict_keys():
    r = hajj_savings.calculate(10_000, 5)
    d = r.to_dict()
    for key in ["hajj_cost_target", "years_to_hajj", "current_savings",
                "expected_annual_return", "monthly_contribution_needed",
                "total_contribution", "expected_growth",
                "target_met_at_zero_contribution"]:
        assert key in d


# --- Validation ---

def test_negative_target_rejected():
    with pytest.raises(ValueError, match="hajj_cost_target"):
        hajj_savings.calculate(-1, 5)


def test_zero_target_rejected():
    with pytest.raises(ValueError, match="hajj_cost_target"):
        hajj_savings.calculate(0, 5)


def test_zero_years_rejected():
    with pytest.raises(ValueError, match="years_to_hajj"):
        hajj_savings.calculate(10_000, 0)


def test_negative_years_rejected():
    with pytest.raises(ValueError, match="years_to_hajj"):
        hajj_savings.calculate(10_000, -1)


def test_negative_savings_rejected():
    with pytest.raises(ValueError, match="current_savings"):
        hajj_savings.calculate(10_000, 5, current_savings=-1)


def test_negative_return_rejected():
    with pytest.raises(ValueError, match="expected_annual_return"):
        hajj_savings.calculate(10_000, 5, expected_annual_return=-0.01)
