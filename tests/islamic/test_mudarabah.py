"""Tests for mudarabah (profit-sharing investment)."""

import pytest

from calcnook.core.islamic import mudarabah


# --- Profit scenarios ---

def test_profit_split_70_30():
    r = mudarabah.calculate(100_000, 20_000, 0.70)
    assert round(r.investor_profit, 2) == 14_000.00
    assert round(r.manager_profit, 2) == 6_000.00
    assert round(r.investor_total, 2) == 114_000.00


def test_profit_split_50_50():
    r = mudarabah.calculate(50_000, 10_000, 0.50)
    assert round(r.investor_profit, 2) == 5_000.00
    assert round(r.manager_profit, 2) == 5_000.00


def test_investor_takes_all():
    # ratio = 1.0 → investor gets 100% of profit
    r = mudarabah.calculate(10_000, 5_000, 1.0)
    assert round(r.investor_profit, 2) == 5_000.00
    assert round(r.manager_profit, 2) == 0.00


def test_zero_profit():
    r = mudarabah.calculate(10_000, 0.0, 0.70)
    assert r.investor_profit == 0.0
    assert r.manager_profit == 0.0
    assert round(r.investor_total, 2) == 10_000.00


# --- Loss scenario ---

def test_loss_borne_by_investor_only():
    r = mudarabah.calculate(100_000, -15_000, 0.70)
    # Full loss = -15000 to investor
    assert round(r.investor_profit, 2) == -15_000.00
    assert round(r.manager_profit, 2) == 0.00
    assert round(r.investor_total, 2) == 85_000.00


def test_total_loss():
    r = mudarabah.calculate(50_000, -50_000, 0.80)
    assert round(r.investor_total, 2) == 0.00


# --- Annualised return ---

def test_annualised_return_computed_when_years_given():
    r = mudarabah.calculate(100_000, 20_000, 0.70, years=3)
    # investor_total = 114000; CAGR = (114000/100000)^(1/3) - 1 ≈ 4.45%
    assert r.annualised_return is not None
    assert round(r.annualised_return, 4) == round((114_000 / 100_000) ** (1 / 3) - 1, 4)


def test_annualised_return_none_when_years_not_given():
    r = mudarabah.calculate(100_000, 20_000, 0.70)
    assert r.annualised_return is None


def test_annualised_return_negative_on_loss():
    r = mudarabah.calculate(100_000, -30_000, 0.70, years=2)
    # investor_total = 70000 → ratio = 0.70; annualised_return < 0
    assert r.annualised_return is not None
    assert r.annualised_return < 0


# --- to_dict ---

def test_to_dict_keys():
    r = mudarabah.calculate(100_000, 20_000, 0.70, years=3)
    d = r.to_dict()
    for key in ["capital", "actual_profit_amount", "investor_share_ratio",
                "investor_profit", "manager_profit", "investor_total",
                "years", "annualised_return"]:
        assert key in d


# --- Validation ---

def test_zero_capital_rejected():
    with pytest.raises(ValueError, match="capital"):
        mudarabah.calculate(0, 1000, 0.70)


def test_negative_capital_rejected():
    with pytest.raises(ValueError, match="capital"):
        mudarabah.calculate(-1, 1000, 0.70)


def test_ratio_zero_rejected():
    with pytest.raises(ValueError, match="investor_share_ratio"):
        mudarabah.calculate(10_000, 1000, 0.0)


def test_ratio_above_one_rejected():
    with pytest.raises(ValueError, match="investor_share_ratio"):
        mudarabah.calculate(10_000, 1000, 1.1)


def test_negative_years_rejected():
    with pytest.raises(ValueError, match="years"):
        mudarabah.calculate(10_000, 1000, 0.70, years=-1)


def test_zero_years_rejected():
    with pytest.raises(ValueError, match="years"):
        mudarabah.calculate(10_000, 1000, 0.70, years=0)
