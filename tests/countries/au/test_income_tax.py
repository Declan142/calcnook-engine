"""Tests for Australia income tax + Medicare + HECS 2025/26."""

import pytest

from calcnook.countries.au import income_tax


def test_below_tax_free_threshold():
    r = income_tax.calculate(15_000)
    assert r.income_tax == 0.0
    assert r.medicare_levy == 0.0


def test_45k_lower_bracket():
    # 18201 to 45000: 16% on (45000-18200)=26800 → 4288
    r = income_tax.calculate(45_000)
    assert round(r.income_tax, 2) == pytest.approx(4288.0, abs=5.0)


def test_80k_mid_bracket():
    # 18201-45000 @ 16%: 26800 * 0.16 = 4288
    # 45001-80000 @ 30%: 35000 * 0.30 = 10500
    # Total = 14788
    r = income_tax.calculate(80_000)
    assert round(r.income_tax, 2) == pytest.approx(14_788.0, abs=5.0)
    # Medicare: 80000 * 2% = 1600
    assert round(r.medicare_levy, 2) == pytest.approx(1600.0, abs=5.0)


def test_hecs_applied():
    r = income_tax.calculate(80_000, has_hecs_debt=True)
    assert r.hecs_repayment > 0
    # 80K is in (79347, 84108) band @ 4%; 80000 * 0.04 = 3200
    assert r.hecs_repayment == pytest.approx(80_000 * 0.04, abs=50)


def test_no_hecs():
    r = income_tax.calculate(80_000, has_hecs_debt=False)
    assert r.hecs_repayment == 0.0


def test_take_home():
    r = income_tax.calculate(60_000)
    assert round(r.take_home, 2) == round(r.gross_income - r.total_tax, 2)


def test_high_income():
    r = income_tax.calculate(200_000)
    # Above 190K: 45%
    rates = [b.rate for b in r.bracket_breakdown]
    assert 0.45 in rates


def test_zero_income():
    r = income_tax.calculate(0)
    assert r.income_tax == 0.0
    assert r.total_tax == 0.0


def test_to_dict():
    r = income_tax.calculate(100_000)
    d = r.to_dict()
    assert "income_tax" in d
    assert "medicare_levy" in d
    assert "hecs_repayment" in d
    assert "take_home" in d


def test_negative_income():
    with pytest.raises(ValueError, match="income"):
        income_tax.calculate(-1)


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(50_000, year=2025)
