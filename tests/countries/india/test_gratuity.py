"""Tests for India Gratuity — Payment of Gratuity Act, 1972."""

import pytest

from calcnook.countries.india import gratuity


def test_standard_10_years():
    """50K basic × 10 yrs → (15 × 50000 × 10) / 26 = 288461.54"""
    r = gratuity.calculate(monthly_basic_salary=50_000, years_of_service=10)
    assert r.years_of_service_used == 10
    assert r.gratuity_gross == pytest.approx(288_461.54, rel=1e-3)
    assert r.exempt_amount == pytest.approx(288_461.54, rel=1e-3)  # under ₹20L cap
    assert r.taxable_amount == 0.0


def test_fractional_years_floored():
    """7.5 years → uses 7 (floor per spec)."""
    r = gratuity.calculate(monthly_basic_salary=40_000, years_of_service=7.5)
    assert r.years_of_service_used == 7
    expected = (15 * 40_000 * 7) / 26.0
    assert r.gratuity_gross == pytest.approx(expected, rel=1e-6)


def test_high_salary_caps_at_20L():
    """5L basic × 30 years → way over ₹20L cap; exempt limited."""
    r = gratuity.calculate(monthly_basic_salary=500_000, years_of_service=30)
    # Gross: (15 × 500000 × 30) / 26 = 8,653,846.15
    assert r.gratuity_gross == pytest.approx(8_653_846.15, rel=1e-3)
    assert r.exempt_amount == pytest.approx(2_000_000.0)
    assert r.taxable_amount == pytest.approx(r.gratuity_gross - 2_000_000.0, rel=1e-3)


def test_with_dearness_allowance():
    r = gratuity.calculate(monthly_basic_salary=40_000, years_of_service=10, dearness_allowance=10_000)
    expected = (15 * 50_000 * 10) / 26.0
    assert r.gratuity_gross == pytest.approx(expected, rel=1e-6)


def test_negative_basic_raises():
    with pytest.raises(ValueError, match="monthly_basic_salary"):
        gratuity.calculate(monthly_basic_salary=-1, years_of_service=10)
