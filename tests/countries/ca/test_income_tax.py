"""Tests for Canada federal income tax 2026."""

import pytest

from calcnook.countries.ca import income_tax


def test_50k():
    # 50K fully in 15% bracket
    # Tax = 50000 * 15% = 7500
    # BPA credit = 16500 * 15% = 2475
    # Net = 7500 - 2475 = 5025
    r = income_tax.calculate(50_000)
    assert r.gross_income == 50_000.0
    assert round(r.basic_personal_credit, 2) == pytest.approx(2475.0)
    assert round(r.tax_owed, 2) == pytest.approx(5025.0, abs=1.0)
    assert r.marginal_rate == 0.15


def test_100k():
    r = income_tax.calculate(100_000)
    assert r.marginal_rate == 0.205
    assert r.tax_owed > 0
    assert r.effective_rate < 0.205


def test_250k():
    r = income_tax.calculate(250_000)
    assert r.marginal_rate == 0.29
    assert r.effective_rate < 0.29


def test_province_stub():
    r = income_tax.calculate(100_000, province="ON")
    assert r.province == "ON"
    assert r.provincial_tax == 0.0  # TODO stub


def test_zero_income():
    r = income_tax.calculate(0)
    assert r.tax_owed == 0.0


def test_effective_rate_reasonable():
    r = income_tax.calculate(80_000)
    assert 0 < r.effective_rate < 0.20


def test_to_dict():
    r = income_tax.calculate(100_000)
    d = r.to_dict()
    assert "tax_owed" in d
    assert "bracket_breakdown" in d
    assert "basic_personal_credit" in d
    assert "provincial_tax" in d


def test_negative_income():
    with pytest.raises(ValueError, match="income"):
        income_tax.calculate(-100)


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(100_000, year=2025)
