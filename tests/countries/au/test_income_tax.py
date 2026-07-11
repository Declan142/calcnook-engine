"""Tests for Australia income tax + Medicare + HECS FY 2026/27."""

import pytest

from calcnook.countries.au import income_tax


def test_below_tax_free_threshold():
    r = income_tax.calculate(15_000)
    assert r.income_tax == 0.0
    assert r.medicare_levy == 0.0
    assert r.bracket_breakdown[0].income_in_bracket == 15_000


def test_45k_lower_bracket():
    # 18201 to 45000: 15% on (45000 - 18200) = 26800, giving 4020
    r = income_tax.calculate(45_000)
    assert r.income_tax == pytest.approx(4_020.0)
    assert r.bracket_breakdown[0].income_in_bracket == 18_200
    assert sum(b.income_in_bracket for b in r.bracket_breakdown) == 45_000


def test_80k_mid_bracket():
    # 18201 to 45000: 26800 * 0.15 = 4020
    # 45001 to 80000: 35000 * 0.30 = 10500
    # Income tax = 14520
    r = income_tax.calculate(80_000)
    assert r.income_tax == pytest.approx(14_520.0)
    assert r.medicare_levy == pytest.approx(1_600.0)


def test_resident_bracket_base_amounts():
    assert income_tax.calculate(135_000).income_tax == pytest.approx(31_020.0)
    assert income_tax.calculate(190_000).income_tax == pytest.approx(51_370.0)
    assert income_tax.calculate(200_000).income_tax == pytest.approx(55_870.0)


def test_hecs_applied():
    r = income_tax.calculate(80_000, has_hecs_debt=True)
    # (80000 - 69528) * 0.15 = 1570.80
    assert r.hecs_repayment == pytest.approx(1_570.80)
    assert r.total_tax == pytest.approx(17_690.80)
    assert r.take_home == pytest.approx(62_309.20)


def test_hecs_current_marginal_thresholds():
    assert income_tax.calculate(69_528, has_hecs_debt=True).hecs_repayment == 0
    assert income_tax.calculate(150_000, has_hecs_debt=True).hecs_repayment == pytest.approx(
        9_028 + (150_000 - 129_717) * 0.17
    )
    assert income_tax.calculate(200_000, has_hecs_debt=True).hecs_repayment == pytest.approx(
        20_000
    )


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
    assert r.bracket_breakdown[0].income_in_bracket == 0


def test_to_dict():
    r = income_tax.calculate(100_000)
    d = r.to_dict()
    assert d["year"] == 2027
    assert "income_tax" in d
    assert "medicare_levy" in d
    assert "hecs_repayment" in d
    assert "take_home" in d


def test_negative_income():
    with pytest.raises(ValueError, match="income"):
        income_tax.calculate(-1)


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(50_000, year=2026)
