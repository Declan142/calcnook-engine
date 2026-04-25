"""Tests for loan_payment (EMI / mortgage amortization)."""

import pytest

from calcnook.core import loan_payment


def test_30yr_mortgage_emi():
    # 300k @ 6.5% for 30 years — well-known reference
    # r = 0.065/12, n = 360
    r = 0.065 / 12
    n = 360
    expected_emi = 300_000 * r * (1 + r) ** n / ((1 + r) ** n - 1)
    result = loan_payment.calculate(300_000, 0.065, 30)
    assert result.monthly_payment == pytest.approx(expected_emi, rel=1e-4)


def test_30yr_mortgage_total_interest_positive():
    result = loan_payment.calculate(300_000, 0.065, 30)
    assert result.total_interest > 0
    assert result.total_payment > result.principal


def test_zero_rate_loan():
    # 0% loan: EMI = principal / n
    result = loan_payment.calculate(120_000, 0.0, 10)
    assert result.monthly_payment == pytest.approx(1000.0, rel=1e-6)
    assert result.total_payment == pytest.approx(120_000.0, rel=1e-6)
    assert result.total_interest == pytest.approx(0.0, abs=1e-6)


def test_1y_short_loan():
    # 12k @ 10% for 1 year
    r = 0.10 / 12
    n = 12
    expected_emi = 12_000 * r * (1 + r) ** n / ((1 + r) ** n - 1)
    result = loan_payment.calculate(12_000, 0.10, 1)
    assert result.monthly_payment == pytest.approx(expected_emi, rel=1e-4)


def test_schedule_structure():
    result = loan_payment.calculate(100_000, 0.08, 5, include_schedule=True)
    assert len(result.amortization) > 0
    first = result.amortization[0]
    assert "month" in first
    assert "principal_paid" in first
    assert "interest_paid" in first
    assert "balance" in first
    # First month balance should be less than principal
    assert first["balance"] < 100_000


def test_schedule_month_count():
    result = loan_payment.calculate(100_000, 0.08, 5, include_schedule=True)
    assert len(result.amortization) == 60  # 5 * 12


def test_schedule_balance_decreases():
    result = loan_payment.calculate(50_000, 0.07, 3, include_schedule=True)
    balances = [row["balance"] for row in result.amortization]
    assert all(balances[i] >= balances[i + 1] for i in range(len(balances) - 1))


def test_no_schedule_by_default():
    result = loan_payment.calculate(100_000, 0.07, 10)
    assert result.amortization == []


def test_to_dict_no_amortization_key():
    result = loan_payment.calculate(100_000, 0.07, 10)
    d = result.to_dict()
    assert "amortization" not in d


def test_to_dict_with_amortization():
    result = loan_payment.calculate(100_000, 0.07, 10, include_schedule=True)
    d = result.to_dict()
    assert "amortization" in d
    assert isinstance(d["amortization"], list)


def test_invalid_principal_rejected():
    with pytest.raises(ValueError, match="principal"):
        loan_payment.calculate(0, 0.07, 10)


def test_negative_rate_rejected():
    with pytest.raises(ValueError, match="annual_rate"):
        loan_payment.calculate(100_000, -0.01, 10)


def test_zero_years_rejected():
    with pytest.raises(ValueError, match="years"):
        loan_payment.calculate(100_000, 0.07, 0)


def test_extra_payment_reduces_total():
    normal = loan_payment.calculate(200_000, 0.06, 20, include_schedule=True)
    extra = loan_payment.calculate(200_000, 0.06, 20,
                                   extra_monthly_payment=500, include_schedule=True)
    assert extra.total_interest < normal.total_interest
    assert len(extra.amortization) < len(normal.amortization)
