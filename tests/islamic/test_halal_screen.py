"""Tests for halal_screen (AAOIFI Sharia stock screener)."""

import pytest

from calcnook.core.islamic import halal_screen
from calcnook.core.islamic.halal_screen import HARAM_SECTORS


# --- Compliant cases ---

def test_clean_tech_stock_passes():
    r = halal_screen.screen(
        sector="technology",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,       # 10% — under 33%
        cash_and_interest_securities=50_000,  # 5%  — under 33%
        receivables=200_000,                  # 20% — under 49%
        total_revenue=500_000,
        haram_revenue=10_000,                 # 2% — under 5%
    )
    assert r.is_compliant is True
    assert r.failed_checks == []


def test_compliant_ratios_stored():
    r = halal_screen.screen(
        sector="healthcare",
        market_cap=2_000_000,
        debt_interest_bearing=400_000,
        cash_and_interest_securities=300_000,
        receivables=600_000,
        total_revenue=1_000_000,
        haram_revenue=30_000,  # 3%
    )
    assert r.is_compliant is True
    assert round(r.ratios["debt_ratio"], 4) == round(400_000 / 2_000_000, 4)
    assert round(r.ratios["haram_revenue_ratio"], 4) == round(30_000 / 1_000_000, 4)


def test_haram_revenue_exactly_at_threshold_passes():
    # 5% exactly == threshold — NOT strictly greater than → should pass
    r = halal_screen.screen(
        sector="retail",
        market_cap=1_000_000,
        debt_interest_bearing=0,
        cash_and_interest_securities=0,
        receivables=0,
        total_revenue=100_000,
        haram_revenue=5_000,  # exactly 5%
    )
    assert r.is_compliant is True


# --- Failing cases ---

def test_bank_sector_fails():
    r = halal_screen.screen(
        sector="banking",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=500_000,
        haram_revenue=0,
    )
    assert r.is_compliant is False
    assert any("haram_sector" in c for c in r.failed_checks)


def test_high_debt_company_fails():
    # debt = 400k / market cap 1M = 40% > 33%
    r = halal_screen.screen(
        sector="manufacturing",
        market_cap=1_000_000,
        debt_interest_bearing=400_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=500_000,
        haram_revenue=0,
    )
    assert r.is_compliant is False
    assert any("debt_ratio" in c for c in r.failed_checks)


def test_high_cash_securities_fails():
    # cash = 400k / 1M = 40% > 33%
    r = halal_screen.screen(
        sector="manufacturing",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=400_000,
        receivables=200_000,
        total_revenue=500_000,
        haram_revenue=0,
    )
    assert r.is_compliant is False
    assert any("cash_ratio" in c for c in r.failed_checks)


def test_high_receivables_fails():
    # receivables = 600k / 1M = 60% > 49%
    r = halal_screen.screen(
        sector="logistics",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=600_000,
        total_revenue=500_000,
        haram_revenue=0,
    )
    assert r.is_compliant is False
    assert any("receivables_ratio" in c for c in r.failed_checks)


def test_haram_revenue_6pct_fails():
    r = halal_screen.screen(
        sector="food",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=100_000,
        haram_revenue=6_000,  # 6% > 5%
    )
    assert r.is_compliant is False
    assert any("haram_revenue_ratio" in c for c in r.failed_checks)


def test_haram_revenue_3pct_passes():
    r = halal_screen.screen(
        sector="food",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=100_000,
        haram_revenue=3_000,  # 3% under 5%
    )
    assert r.is_compliant is True


def test_multiple_failures_reported():
    r = halal_screen.screen(
        sector="gambling",
        market_cap=500_000,
        debt_interest_bearing=400_000,  # 80% debt
        cash_and_interest_securities=50_000,
        receivables=100_000,
        total_revenue=200_000,
        haram_revenue=100_000,  # 50% haram
    )
    assert r.is_compliant is False
    assert len(r.failed_checks) >= 3  # sector + debt + haram revenue at minimum


# --- Purification ratio ---

def test_purification_ratio_correct():
    r = halal_screen.screen(
        sector="technology",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=500_000,
        haram_revenue=15_000,  # 3%
    )
    assert round(r.purification_ratio, 4) == round(15_000 / 500_000, 4)


# --- Sector matching ---

def test_case_insensitive_sector_match():
    r = halal_screen.screen(
        sector="Alcohol",
        market_cap=1_000_000,
        debt_interest_bearing=0,
        cash_and_interest_securities=0,
        receivables=0,
        total_revenue=100_000,
        haram_revenue=0,
    )
    assert r.is_compliant is False


def test_haram_sectors_constant_is_tuple():
    assert isinstance(HARAM_SECTORS, tuple)
    assert "alcohol" in HARAM_SECTORS
    assert "gambling" in HARAM_SECTORS


# --- to_dict ---

def test_to_dict_keys():
    r = halal_screen.screen(
        sector="technology",
        market_cap=1_000_000,
        debt_interest_bearing=100_000,
        cash_and_interest_securities=50_000,
        receivables=200_000,
        total_revenue=500_000,
        haram_revenue=10_000,
    )
    d = r.to_dict()
    assert "is_compliant" in d
    assert "failed_checks" in d
    assert "ratios" in d
    assert "purification_ratio" in d


# --- Validation ---

def test_zero_market_cap_rejected():
    with pytest.raises(ValueError, match="market_cap"):
        halal_screen.screen("tech", 0, 0, 0, 0, 100_000, 0)


def test_negative_debt_rejected():
    with pytest.raises(ValueError, match="debt_interest_bearing"):
        halal_screen.screen("tech", 1_000_000, -1, 0, 0, 100_000, 0)


def test_zero_total_revenue_rejected():
    with pytest.raises(ValueError, match="total_revenue"):
        halal_screen.screen("tech", 1_000_000, 0, 0, 0, 0, 0)


def test_haram_revenue_exceeds_total_rejected():
    with pytest.raises(ValueError, match="haram_revenue"):
        halal_screen.screen("tech", 1_000_000, 0, 0, 0, 100_000, 200_000)
