"""Tests for US retirement account calculators 2026."""

import pytest

from calcnook.countries.us import retirement_accounts


# ---------------------------------------------------------------------------
# 401(k) tests
# ---------------------------------------------------------------------------

def test_401k_basic_with_employer_match():
    # 50% match up to 6% of 80K salary = employer matches up to 4.8K salary
    # employee contributes 10K < 24K limit → match = 0.5 * min(10000, 4800) = 2400
    r = retirement_accounts.traditional_401k(
        contribution=10_000, salary=80_000,
        employer_match_percent=0.50, employer_match_cap=0.06,
        age=35, marginal_tax_rate=0.22
    )
    assert r.employee_contribution == 10_000.0
    assert r.employer_contribution == pytest.approx(2_400.0)
    assert r.total_contribution == pytest.approx(12_400.0)
    assert r.tax_savings_now == pytest.approx(2_200.0)
    assert r.age == 35
    assert not r.is_employee_maxed


def test_401k_over_limit_capped():
    # Try to contribute more than 24K limit (under 50)
    r = retirement_accounts.traditional_401k(
        contribution=30_000, salary=120_000,
        employer_match_percent=0.50, employer_match_cap=0.06,
        age=40
    )
    assert r.employee_contribution == 24_000.0
    assert r.is_employee_maxed is True


def test_401k_catch_up_50_plus():
    r = retirement_accounts.traditional_401k(
        contribution=35_000, salary=100_000,
        employer_match_percent=0, employer_match_cap=0,
        age=52
    )
    assert r.employee_limit == 32_000.0
    assert r.employee_contribution == 32_000.0
    assert r.is_employee_maxed is True


def test_401k_to_dict():
    r = retirement_accounts.traditional_401k(
        10_000, 80_000, 0.5, 0.06, 35
    )
    d = r.to_dict()
    assert "employee_contribution" in d
    assert "tax_savings_now" in d


def test_401k_invalid_contribution():
    with pytest.raises(ValueError, match="contribution"):
        retirement_accounts.traditional_401k(-1, 80_000, 0.5, 0.06, 35)


# ---------------------------------------------------------------------------
# Roth IRA tests
# ---------------------------------------------------------------------------

def test_roth_fully_eligible():
    r = retirement_accounts.roth_ira(7_000, age=30, magi=100_000, filing_status="single")
    assert r.effective_contribution == 7_000.0
    assert r.phase_out_factor == 1.0


def test_roth_mid_phaseout():
    # Single, MAGI 157,500 — midpoint of 150K-165K
    r = retirement_accounts.roth_ira(7_000, age=30, magi=157_500, filing_status="single")
    assert round(r.phase_out_factor, 4) == pytest.approx(0.5, abs=0.01)
    assert round(r.effective_contribution, 2) == pytest.approx(3_500.0, abs=10)


def test_roth_fully_phased_out():
    r = retirement_accounts.roth_ira(7_000, age=30, magi=170_000, filing_status="single")
    assert r.phase_out_factor == 0.0
    assert r.effective_contribution == 0.0


def test_roth_catch_up_50():
    r = retirement_accounts.roth_ira(8_000, age=52, magi=50_000, filing_status="single")
    assert r.contribution_limit == 8_000.0
    assert r.effective_contribution == 8_000.0


def test_roth_mfj_phaseout():
    # MFJ: 236K-246K range; test at 241K (midpoint)
    r = retirement_accounts.roth_ira(7_000, age=40, magi=241_000, filing_status="married_jointly")
    assert 0 < r.phase_out_factor < 1


def test_roth_to_dict():
    r = retirement_accounts.roth_ira(7_000, 35, 120_000, "single")
    d = r.to_dict()
    assert "effective_contribution" in d
    assert "phase_out_factor" in d


def test_roth_invalid_filing_status():
    with pytest.raises(ValueError, match="filing_status"):
        retirement_accounts.roth_ira(7_000, 35, 120_000, "partner")


def test_roth_contribution_over_limit_capped():
    r = retirement_accounts.roth_ira(10_000, age=30, magi=50_000, filing_status="single")
    assert r.effective_contribution == 7_000.0  # capped at limit
