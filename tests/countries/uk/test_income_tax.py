"""Tests for UK income tax + National Insurance 2025/26."""

import pytest

from calcnook.countries.uk import income_tax


def test_30k_basic_rate():
    # 30K income, PA = 12570, taxable = 17430, all in basic rate
    # IT = 17430 * 20% = 3486
    # NI: (30000-12570)*8% = 17430*8% = 1394.4
    r = income_tax.calculate(30_000)
    assert round(r.income_tax, 2) == pytest.approx(3486.0)
    assert round(r.national_insurance, 2) == pytest.approx(1394.40, abs=1.0)
    assert r.personal_allowance_used == income_tax.PERSONAL_ALLOWANCE
    assert r.year == 2026


def test_60k_higher_rate():
    # 60K: taxable = 60000-12570=47430
    # basic band: 37700 * 20% = 7540
    # higher band: (47430-37700)*40% = 9730*40% = 3892
    # IT total = 11432
    r = income_tax.calculate(60_000)
    assert round(r.income_tax, 2) == pytest.approx(11432.0, abs=2.0)


def test_130k_allowance_taper():
    # Income 130K: reduction = (130000-100000)/2 = 15000
    # PA = 12570 - 15000 → capped at 0 → PA = 0
    # taxable = 130000
    r = income_tax.calculate(130_000)
    assert r.personal_allowance_used == 0.0
    assert r.taxable_income == 130_000.0


def test_100k_no_taper():
    # Exactly at 100K — no taper
    r = income_tax.calculate(100_000)
    assert r.personal_allowance_used == income_tax.PERSONAL_ALLOWANCE


def test_200k_additional_rate():
    r = income_tax.calculate(200_000)
    # Should have additional rate bracket entry
    rates = [b.rate for b in r.bracket_breakdown]
    assert income_tax.ADDITIONAL_RATE in rates


def test_take_home_equals_income_minus_total_tax():
    r = income_tax.calculate(50_000)
    assert round(r.take_home, 2) == round(r.gross_income - r.total_tax, 2)


def test_zero_income():
    r = income_tax.calculate(0)
    assert r.income_tax == 0.0
    assert r.national_insurance == 0.0


def test_to_dict():
    r = income_tax.calculate(40_000)
    d = r.to_dict()
    assert "income_tax" in d
    assert "national_insurance" in d
    assert "take_home" in d
    assert "bracket_breakdown" in d


def test_negative_income():
    with pytest.raises(ValueError, match="income"):
        income_tax.calculate(-100)


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(50_000, year=2024)


# Helper to avoid attribute error — UK result doesn't have marginal_rate
# Testing the above calls don't error is sufficient
def test_no_crash_various_incomes():
    for inc in [0, 12_570, 20_000, 50_270, 100_000, 125_140, 200_000]:
        r = income_tax.calculate(inc)
        assert r.total_tax >= 0
