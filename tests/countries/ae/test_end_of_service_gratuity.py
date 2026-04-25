"""Tests for UAE End of Service Gratuity."""

import pytest

from calcnook.countries.ae import end_of_service_gratuity as eosg


def test_5_years_8k_salary():
    # 5 years, 21 days/year
    # daily wage = 8000/30 = 266.67
    # gratuity = 5 * 21 * 266.67 = 28000
    r = eosg.calculate(monthly_basic_salary=8_000, years_of_service=5)
    assert round(r.gratuity_aed, 2) == pytest.approx(28_000.0, abs=1.0)
    assert r.is_capped is False


def test_10_years_8k_salary():
    # First 5 years: 5 * 21 * (8000/30) = 28000
    # Next 5 years: 5 * 30 * (8000/30) = 40000
    # Total = 68000, cap = 24 * 8000 = 192000 → not capped
    r = eosg.calculate(monthly_basic_salary=8_000, years_of_service=10)
    assert round(r.gratuity_aed, 2) == pytest.approx(68_000.0, abs=1.0)
    assert r.is_capped is False


def test_cap_applied_long_tenure():
    # Very long service: 50 years at 10K/month
    # First 5: 5*21*(10000/30)=35000; Next 45: 45*30*(10000/30)=450000
    # Total = 485000, cap = 24*10000 = 240000 → capped
    r = eosg.calculate(monthly_basic_salary=10_000, years_of_service=50)
    assert r.is_capped is True
    assert round(r.gratuity_aed, 2) == pytest.approx(240_000.0)


def test_under_1_year_no_gratuity():
    r = eosg.calculate(monthly_basic_salary=8_000, years_of_service=0.5)
    assert r.gratuity_aed == 0.0
    assert r.formula_used == "no_gratuity_under_1_year"


def test_exactly_1_year():
    r = eosg.calculate(monthly_basic_salary=6_000, years_of_service=1)
    # 1 * 21 * (6000/30) = 4200
    assert round(r.gratuity_aed, 2) == pytest.approx(4_200.0, abs=1.0)


def test_unlimited_contract_same_result():
    r1 = eosg.calculate(8_000, 5, contract_type="limited")
    r2 = eosg.calculate(8_000, 5, contract_type="unlimited")
    assert r1.gratuity_aed == r2.gratuity_aed


def test_to_dict():
    r = eosg.calculate(8_000, 5)
    d = r.to_dict()
    assert "gratuity_aed" in d
    assert "is_capped" in d
    assert "daily_basic_wage" in d


def test_negative_salary():
    with pytest.raises(ValueError, match="monthly_basic_salary"):
        eosg.calculate(-1, 5)


def test_negative_years():
    with pytest.raises(ValueError, match="years_of_service"):
        eosg.calculate(8_000, -1)


def test_invalid_contract_type():
    with pytest.raises(ValueError, match="contract_type"):
        eosg.calculate(8_000, 5, contract_type="freelance")
