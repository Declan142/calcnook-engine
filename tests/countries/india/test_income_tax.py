"""Tests for India income tax — New Regime FY 2025-26 (AY 2026-27)."""

import pytest

from calcnook.countries.india import income_tax


def test_5L_new_regime():
    # 5L gross - 75K std deduction = 4.25L taxable
    # nil on first 4L; 5% on (4.25L-4L)=25000 → 1250
    # taxable 4.25L < 12L → full 87A rebate (max 60K); rebate = min(1250, 60000) = 1250
    # cess = 0; tax = 0
    r = income_tax.calculate(500_000)
    assert r.taxable_income == 425_000.0
    assert r.tax_owed == 0.0   # rebate covers it
    assert r.rebate_87a > 0


def test_10L_new_regime():
    # 10L - 75K = 9.25L taxable
    # Nil on 4L; 5% on (8L-4L)=4L→20K; 10% on (9.25L-8L)=1.25L→12500
    # Tax before rebate = 32500
    # taxable 9.25L < 12L → rebate = min(32500, 60000) = 32500 → tax_after = 0
    r = income_tax.calculate(1_000_000)
    assert r.tax_owed == 0.0


def test_12L_exact_rebate_boundary():
    # 12L - 75K = 11.25L taxable (< 12L) → still gets rebate
    r = income_tax.calculate(1_200_000)
    assert r.taxable_income == 1_125_000.0
    assert r.rebate_87a > 0
    # Tax should be 0 since taxable < 12L
    assert r.tax_owed == 0.0


def test_15L_above_rebate():
    # 15L - 75K = 14.25L taxable > 12L → no 87A rebate
    # Nil on 4L; 5% on 4L=20K; 10% on 4L=40K; 15% on (14.25L-12L)=2.25L=33750
    # Tax before rebate = 93750, no rebate
    # cess = 93750 * 4% = 3750; total = 97500
    r = income_tax.calculate(1_500_000)
    assert r.rebate_87a == 0.0
    assert r.tax_owed == pytest.approx(97_500.0, abs=500)
    assert r.health_education_cess > 0


def test_25L_top_bracket():
    # 25L - 75K = 24.25L taxable
    # Nil on 4L; 5% on 4L; 10% on 4L; 15% on 4L; 20% on 4L; 25% on 4L; 30% on 0.25L
    r = income_tax.calculate(2_500_000)
    assert r.marginal_rate == 0.30
    assert r.tax_owed > 0


def test_regime_new_is_default():
    r = income_tax.calculate(1_000_000)
    assert r.regime == "new"


def test_old_regime_stub():
    r = income_tax.calculate(1_000_000, regime="old")
    assert r.regime == "old"
    assert r.standard_deduction == 50_000.0


def test_to_dict():
    r = income_tax.calculate(1_500_000)
    d = r.to_dict()
    assert "tax_owed" in d
    assert "rebate_87a" in d
    assert "health_education_cess" in d


def test_negative_income():
    with pytest.raises(ValueError, match="gross_income"):
        income_tax.calculate(-1)


def test_invalid_regime():
    with pytest.raises(ValueError, match="regime"):
        income_tax.calculate(1_000_000, regime="flat")


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(1_000_000, year=2025)
