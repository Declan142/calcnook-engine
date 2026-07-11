"""Tests for US retirement account calculators 2026."""

import pytest

from calcnook.countries.us import retirement_accounts


# ---------------------------------------------------------------------------
# 401(k) tests
# ---------------------------------------------------------------------------

def test_401k_basic_with_employer_match():
    # 50% match up to 6% of 80K salary = employer matches up to 4.8K salary
    # Employee contributes $10,000 below the $24,500 limit.
    # Match = 0.5 * min(10,000, 4,800) = 2,400.
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
    # Try to contribute more than the $24,500 limit for an employee under 50.
    r = retirement_accounts.traditional_401k(
        contribution=30_000, salary=120_000,
        employer_match_percent=0.50, employer_match_cap=0.06,
        age=40
    )
    assert r.employee_limit == 24_500.0
    assert r.employee_contribution == 24_500.0
    assert r.annual_additions_limit == 72_000.0
    assert r.total_limit == 72_000.0
    assert r.is_employee_maxed is True


def test_401k_catch_up_50_plus():
    r = retirement_accounts.traditional_401k(
        contribution=35_000, salary=100_000,
        employer_match_percent=0, employer_match_cap=0,
        age=52
    )
    assert r.catch_up_limit == 8_000.0
    assert r.employee_limit == 32_500.0
    assert r.employee_contribution == 32_500.0
    assert r.total_limit == 80_000.0
    assert r.is_employee_maxed is True


def test_401k_age_60_to_63_super_catch_up_and_compensation_cap():
    # Employee = 24,500 + 11,250 = 35,750.
    # Match compensation = min(500,000, 360,000) = 360,000.
    # Employer = 50% * min(35,750, 6% * 360,000) = 10,800.
    # Total = 35,750 + 10,800 = 46,550; tax savings = 35,750 * 24% = 8,580.
    r = retirement_accounts.traditional_401k(
        contribution=40_000, salary=500_000,
        employer_match_percent=0.50, employer_match_cap=0.06,
        age=61, marginal_tax_rate=0.24,
    )
    assert r.employee_contribution == 35_750.0
    assert r.catch_up_limit == 11_250.0
    assert r.compensation_limit == 360_000.0
    assert r.compensation_used == 360_000.0
    assert r.employer_contribution == pytest.approx(10_800.0)
    assert r.total_contribution == pytest.approx(46_550.0)
    assert r.tax_savings_now == pytest.approx(8_580.0)
    assert r.total_limit == 83_250.0


def test_401k_age_64_returns_to_normal_catch_up():
    r = retirement_accounts.traditional_401k(
        contribution=40_000, salary=100_000,
        employer_match_percent=0, employer_match_cap=0,
        age=64,
    )
    assert r.catch_up_limit == 8_000.0
    assert r.employee_limit == 32_500.0
    assert r.total_limit == 80_000.0


@pytest.mark.parametrize(
    ("age", "catch_up_limit", "total_limit"),
    [
        (49, 0.0, 72_000.0),
        (50, 8_000.0, 80_000.0),
        (59, 8_000.0, 80_000.0),
        (60, 11_250.0, 83_250.0),
        (63, 11_250.0, 83_250.0),
        (64, 8_000.0, 80_000.0),
    ],
)
def test_401k_age_tier_boundaries(age, catch_up_limit, total_limit):
    r = retirement_accounts.traditional_401k(
        contribution=0, salary=0,
        employer_match_percent=0, employer_match_cap=0,
        age=age,
    )
    assert r.catch_up_limit == catch_up_limit
    assert r.total_limit == total_limit


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
    r = retirement_accounts.roth_ira(7_500, age=30, magi=100_000, filing_status="single")
    assert r.contribution_limit == 7_500.0
    assert r.effective_contribution == 7_500.0
    assert r.phase_out_factor == 1.0


def test_roth_mid_phaseout():
    # Single, MAGI 160,500: midpoint of $153,000 to $168,000.
    # Phase-out = 1 - (160,500 - 153,000) / 15,000 = 0.5.
    # Effective contribution = $7,500 * 0.5 = $3,750.
    r = retirement_accounts.roth_ira(7_500, age=30, magi=160_500, filing_status="single")
    assert round(r.phase_out_factor, 4) == pytest.approx(0.5, abs=0.01)
    assert round(r.effective_contribution, 2) == pytest.approx(3_750.0, abs=10)
    assert r.phase_out_low == 153_000.0
    assert r.phase_out_high == 168_000.0


def test_roth_fully_phased_out():
    r = retirement_accounts.roth_ira(7_000, age=30, magi=170_000, filing_status="single")
    assert r.phase_out_factor == 0.0
    assert r.effective_contribution == 0.0


def test_roth_catch_up_50():
    r = retirement_accounts.roth_ira(9_000, age=52, magi=50_000, filing_status="single")
    assert r.contribution_limit == 8_600.0
    assert r.effective_contribution == 8_600.0


def test_roth_mfj_phaseout():
    # MFJ midpoint: 1 - (247,000 - 242,000) / 10,000 = 0.5.
    r = retirement_accounts.roth_ira(7_500, age=40, magi=247_000, filing_status="married_jointly")
    assert r.phase_out_factor == pytest.approx(0.5)
    assert r.phase_out_low == 242_000.0
    assert r.phase_out_high == 252_000.0


@pytest.mark.parametrize(
    ("filing_status", "low", "high"),
    [
        ("single", 153_000.0, 168_000.0),
        ("head_of_household", 153_000.0, 168_000.0),
        ("married_jointly", 242_000.0, 252_000.0),
        ("married_separately", 0.0, 10_000.0),
    ],
)
def test_roth_2026_phaseout_ranges(filing_status, low, high):
    r = retirement_accounts.roth_ira(
        contribution=0,
        age=30,
        magi=0,
        filing_status=filing_status,
    )
    assert r.phase_out_low == low
    assert r.phase_out_high == high


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
    assert r.effective_contribution == 7_500.0  # capped at limit
