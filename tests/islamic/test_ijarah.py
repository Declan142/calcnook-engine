"""Tests for ijarah (Islamic lease-to-own)."""

import pytest

from calcnook.core.islamic import ijarah


# --- Basic calculations ---

def test_total_rent_paid():
    r = ijarah.calculate(30_000, 600.0, 5)
    assert round(r.total_rent_paid, 2) == 36_000.00


def test_total_cost_of_ownership_default_fee():
    # Default transfer_fee = 1.0
    r = ijarah.calculate(30_000, 600.0, 5)
    assert round(r.total_cost_of_ownership, 2) == 36_001.00


def test_total_cost_with_custom_fee():
    r = ijarah.calculate(30_000, 600.0, 5, transfer_fee=500.0)
    assert round(r.total_cost_of_ownership, 2) == 36_500.00


def test_effective_cost_premium():
    r = ijarah.calculate(30_000, 600.0, 5)
    # 36001 - 30000 = 6001
    assert round(r.effective_cost_premium, 2) == 6_001.00


def test_effective_premium_percent():
    r = ijarah.calculate(30_000, 600.0, 5)
    expected_pct = (6_001 / 30_000) * 100
    assert round(r.effective_premium_percent, 4) == round(expected_pct, 4)


def test_zero_monthly_rent():
    # Bank gifts the lease — client only pays transfer fee
    r = ijarah.calculate(20_000, 0.0, 3, transfer_fee=100.0)
    assert round(r.total_rent_paid, 2) == 0.00
    assert round(r.total_cost_of_ownership, 2) == 100.00


def test_zero_transfer_fee():
    r = ijarah.calculate(30_000, 600.0, 5, transfer_fee=0.0)
    assert round(r.total_cost_of_ownership, 2) == 36_000.00


def test_longer_tenure_higher_cost():
    r5 = ijarah.calculate(30_000, 600.0, 5)
    r7 = ijarah.calculate(30_000, 600.0, 7)
    assert r7.total_cost_of_ownership > r5.total_cost_of_ownership


def test_to_dict_keys():
    r = ijarah.calculate(30_000, 600.0, 5)
    d = r.to_dict()
    for key in ["asset_cost", "monthly_rent", "lease_years", "transfer_fee",
                "total_rent_paid", "total_cost_of_ownership",
                "effective_cost_premium", "effective_premium_percent"]:
        assert key in d


# --- Validation ---

def test_negative_asset_cost_rejected():
    with pytest.raises(ValueError, match="asset_cost"):
        ijarah.calculate(-1, 600.0, 5)


def test_zero_asset_cost_rejected():
    with pytest.raises(ValueError, match="asset_cost"):
        ijarah.calculate(0, 600.0, 5)


def test_negative_rent_rejected():
    with pytest.raises(ValueError, match="monthly_rent"):
        ijarah.calculate(30_000, -1.0, 5)


def test_zero_lease_years_rejected():
    with pytest.raises(ValueError, match="lease_years"):
        ijarah.calculate(30_000, 600.0, 0)


def test_negative_transfer_fee_rejected():
    with pytest.raises(ValueError, match="transfer_fee"):
        ijarah.calculate(30_000, 600.0, 5, transfer_fee=-1.0)
