"""Tests for Canada federal income tax 2026."""

import pytest

from calcnook.countries.ca import income_tax


def test_50k():
    # 50K fully in 14% bracket
    # Tax = 50000 * 14% = 7000
    # BPA credit = 16452 * 14% = 2303.28
    # Net = 7000 - 2303.28 = 4696.72
    r = income_tax.calculate(50_000)
    assert r.gross_income == 50_000.0
    assert r.federal_tax_before_credits == pytest.approx(7000.0)
    assert r.basic_personal_credit == pytest.approx(2303.28)
    assert r.tax_owed == pytest.approx(4696.72)
    assert r.marginal_rate == 0.14


def test_100k():
    r = income_tax.calculate(100_000)
    assert r.marginal_rate == 0.205
    assert r.tax_owed > 0
    assert r.effective_rate < 0.205


def test_250k():
    r = income_tax.calculate(250_000)
    assert r.marginal_rate == 0.29
    assert r.effective_rate < 0.29


def test_2026_bracket_thresholds_and_rates():
    r = income_tax.calculate(300_000)
    assert [b.rate for b in r.bracket_breakdown] == [0.14, 0.205, 0.26, 0.29, 0.33]
    assert [b.taxed_in_bracket for b in r.bracket_breakdown] == [
        58_523,
        58_522,
        64_395,
        77_042,
        41_518,
    ]


def test_2026_bpa_taper_and_floor():
    full_credit = 16_452 * 0.14
    minimum_credit = 14_829 * 0.14
    midpoint_income = 200_000
    midpoint_bpa = 16_452 - (midpoint_income - 181_440) * (1_623 / 77_042)

    assert income_tax.calculate(181_440).basic_personal_credit == pytest.approx(full_credit)
    assert income_tax.calculate(midpoint_income).basic_personal_credit == pytest.approx(
        midpoint_bpa * 0.14
    )
    assert income_tax.calculate(258_482).basic_personal_credit == pytest.approx(minimum_credit)
    assert income_tax.calculate(300_000).basic_personal_credit == pytest.approx(minimum_credit)


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
