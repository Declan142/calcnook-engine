"""Tests for US federal income tax 2026."""

import pytest

from calcnook.countries.us import income_tax


def test_single_60k():
    # 60K - 15K std deduction = 45K taxable
    # 10% on 11,925 = 1192.50; 12% on (45000-11925)=33075 → 3969.00 total = 5161.50
    r = income_tax.calculate(60_000, "single")
    assert r.filing_status == "single"
    assert r.year == 2026
    assert round(r.taxable_income, 2) == 45_000.0
    assert round(r.tax_owed, 2) == pytest.approx(5161.50, abs=1.0)


def test_mfj_100k():
    # 100K - 30K std deduction = 70K taxable
    # 10% on 23850 = 2385; 12% on (70000-23850)=46150 → 5538 = 7923
    r = income_tax.calculate(100_000, "married_jointly")
    assert r.taxable_income == 70_000.0
    assert round(r.tax_owed, 2) == pytest.approx(7923.0, abs=1.0)
    assert r.marginal_rate == 0.12


def test_high_earner_single():
    r = income_tax.calculate(700_000, "single")
    assert r.marginal_rate == 0.37
    assert r.effective_rate < 0.37
    assert r.tax_owed > 0


def test_edge_at_bracket():
    # taxable income exactly at first bracket boundary for single
    # std deduction 15K, gross = 11925+15000 = 26925 → taxable = 11925
    r = income_tax.calculate(26_925, "single")
    assert round(r.taxable_income, 2) == 11_925.0
    assert r.marginal_rate == 0.10


def test_head_of_household():
    r = income_tax.calculate(50_000, "head_of_household")
    assert r.filing_status == "head_of_household"
    assert r.year == 2026


def test_married_separately():
    r = income_tax.calculate(80_000, "married_separately")
    assert r.filing_status == "married_separately"


def test_zero_income():
    r = income_tax.calculate(0, "single")
    assert r.tax_owed == 0.0
    assert r.effective_rate == 0.0


def test_effective_rate_less_than_marginal():
    r = income_tax.calculate(200_000, "single")
    assert r.effective_rate < r.marginal_rate


def test_to_dict():
    r = income_tax.calculate(80_000, "single")
    d = r.to_dict()
    assert "tax_owed" in d
    assert "bracket_breakdown" in d
    assert isinstance(d["bracket_breakdown"], list)
    assert d["filing_status"] == "single"


def test_invalid_filing_status():
    with pytest.raises(ValueError, match="filing_status"):
        income_tax.calculate(50_000, "joint")


def test_invalid_year():
    with pytest.raises(ValueError, match="year"):
        income_tax.calculate(50_000, "single", year=2025)


def test_negative_income():
    with pytest.raises(ValueError, match="income"):
        income_tax.calculate(-1, "single")
