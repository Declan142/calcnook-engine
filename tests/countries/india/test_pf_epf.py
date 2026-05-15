"""Tests for India PF/EPF — EPFO scheme + corpus projection."""

import pytest

from calcnook.countries.india import pf_epf


def test_basic_50k_above_cap():
    """₹50K basic: employee on actual basic, employer EPS capped at ₹15K."""
    r = pf_epf.calculate(monthly_basic=50_000, years=30)
    # Employee: 12% of 50K = 6000
    assert r.employee_monthly == pytest.approx(6000.0)
    # Employer total: 12% of min(50K, 15K) = 12% of 15K = 1800
    assert r.employer_monthly == pytest.approx(1800.0)
    # 8.33% × 15K = 1249.5 (EPS)
    assert r.employer_eps_monthly == pytest.approx(1249.5, rel=1e-3)
    # 3.67% × 15K = 550.5 (EPF portion)
    assert r.employer_epf_monthly == pytest.approx(550.5, rel=1e-3)
    # Sum check
    assert r.employer_eps_monthly + r.employer_epf_monthly == pytest.approx(r.employer_monthly, rel=1e-6)
    assert r.corpus_at_retirement > 0


def test_basic_10k_below_cap():
    """₹10K basic: under the ₹15K cap → employer % applies on full basic."""
    r = pf_epf.calculate(monthly_basic=10_000, years=20)
    assert r.employee_monthly == pytest.approx(1200.0)
    # Employer 12% of 10K = 1200 (no cap binding)
    assert r.employer_monthly == pytest.approx(1200.0)
    assert r.employer_eps_monthly == pytest.approx(833.0, rel=1e-3)
    assert r.employer_epf_monthly == pytest.approx(367.0, rel=1e-3)


def test_corpus_grows_with_years():
    short = pf_epf.calculate(monthly_basic=20_000, years=10).corpus_at_retirement
    long = pf_epf.calculate(monthly_basic=20_000, years=30).corpus_at_retirement
    assert long > short * 3  # 3x time, but compounding amplifies


def test_to_dict_keys():
    r = pf_epf.calculate(monthly_basic=15_000, years=25).to_dict()
    for key in (
        "employee_monthly", "employer_monthly", "employer_eps_monthly",
        "employer_epf_monthly", "total_monthly", "corpus_at_retirement", "breakdown",
    ):
        assert key in r


def test_negative_basic_raises():
    with pytest.raises(ValueError, match="monthly_basic"):
        pf_epf.calculate(monthly_basic=-1, years=10)


def test_negative_years_raises():
    with pytest.raises(ValueError, match="years"):
        pf_epf.calculate(monthly_basic=10000, years=-1)
