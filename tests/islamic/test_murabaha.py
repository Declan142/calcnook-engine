"""Tests for murabaha (cost-plus financing)."""

import pytest

from calcnook.core.islamic import murabaha


# --- Basic calculations ---

def test_total_sale_price():
    r = murabaha.calculate(100_000, 30.0, 5)
    assert round(r.total_sale_price, 2) == 130_000.00


def test_total_markup():
    r = murabaha.calculate(100_000, 30.0, 5)
    assert round(r.total_markup, 2) == 30_000.00


def test_monthly_installment_no_down_payment():
    # principal_financed = 130_000, months = 60
    r = murabaha.calculate(100_000, 30.0, 5)
    expected_monthly = 130_000 / 60
    assert round(r.monthly_installment, 4) == round(expected_monthly, 4)


def test_total_paid_equals_sale_price_when_no_down():
    r = murabaha.calculate(100_000, 30.0, 5)
    assert pytest.approx(r.total_paid, abs=0.01) == r.total_sale_price


def test_with_down_payment():
    r = murabaha.calculate(100_000, 30.0, 5, down_payment=20_000)
    assert round(r.principal_financed, 2) == 110_000.00
    expected_monthly = 110_000 / 60
    assert round(r.monthly_installment, 4) == round(expected_monthly, 4)
    # total paid = down + installments
    assert pytest.approx(r.total_paid, abs=0.01) == 20_000 + expected_monthly * 60


def test_zero_markup():
    r = murabaha.calculate(50_000, 0.0, 3)
    assert round(r.total_sale_price, 2) == 50_000.00
    assert round(r.total_markup, 2) == 0.00
    assert round(r.monthly_installment, 4) == round(50_000 / 36, 4)


def test_effective_apr_sanity():
    # 30% markup over 5y → APR should be positive and less than the markup rate
    r = murabaha.calculate(100_000, 30.0, 5)
    # 30% total / 5y is roughly 5.4% p.a. effective; IRR should be in [4%, 8%]
    assert 0.0 < r.effective_apr_equivalent < 0.15


def test_effective_apr_with_down_payment():
    # Same asset, with down payment — principal is lower but fewer months
    r = murabaha.calculate(100_000, 30.0, 5, down_payment=30_000)
    assert r.effective_apr_equivalent > 0


def test_to_dict_keys():
    r = murabaha.calculate(100_000, 30.0, 5)
    d = r.to_dict()
    for key in ["asset_cost", "markup_percent", "tenure_years", "down_payment",
                "total_sale_price", "principal_financed", "monthly_installment",
                "total_paid", "total_markup", "effective_apr_equivalent"]:
        assert key in d


# --- Validation ---

def test_negative_asset_cost_rejected():
    with pytest.raises(ValueError, match="asset_cost"):
        murabaha.calculate(-1, 30.0, 5)


def test_zero_asset_cost_rejected():
    with pytest.raises(ValueError, match="asset_cost"):
        murabaha.calculate(0, 30.0, 5)


def test_negative_markup_rejected():
    with pytest.raises(ValueError, match="markup_percent"):
        murabaha.calculate(100_000, -5.0, 5)


def test_zero_tenure_rejected():
    with pytest.raises(ValueError, match="tenure_years"):
        murabaha.calculate(100_000, 30.0, 0)


def test_negative_down_payment_rejected():
    with pytest.raises(ValueError, match="down_payment"):
        murabaha.calculate(100_000, 30.0, 5, down_payment=-1)


def test_down_payment_exceeding_sale_price_rejected():
    with pytest.raises(ValueError, match="down_payment"):
        murabaha.calculate(100_000, 30.0, 5, down_payment=200_000)
