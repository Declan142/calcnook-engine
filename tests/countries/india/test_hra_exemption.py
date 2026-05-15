"""Tests for India HRA Exemption — Section 10(13A)."""

import pytest

from calcnook.countries.india import hra_exemption


def test_metro_normal_case():
    """₹50K basic, ₹20K HRA, ₹18K rent, metro:
       actual_hra = 20000
       rent - 10% basic = 18000 - 5000 = 13000  ← bound
       50% basic = 25000
       → exempt = 13000
    """
    r = hra_exemption.calculate(
        basic_monthly=50_000,
        hra_received_monthly=20_000,
        rent_paid_monthly=18_000,
        is_metro=True,
    )
    assert r.exempt_monthly == pytest.approx(13_000.0)
    assert r.exempt_annual == pytest.approx(156_000.0)
    assert r.taxable_hra_annual == pytest.approx(20_000 * 12 - 156_000)
    assert r.breakdown["applied_min"] == "rent_minus_10pct_basic"


def test_non_metro_normal_case():
    """₹50K basic, ₹15K HRA, ₹15K rent, non-metro:
       actual_hra = 15000  ← bound (smallest)
       rent - 10% = 15000 - 5000 = 10000  → wait, 10000 < 15000, so this is bound
       40% basic = 20000
       → exempt = 10000
    """
    r = hra_exemption.calculate(
        basic_monthly=50_000,
        hra_received_monthly=15_000,
        rent_paid_monthly=15_000,
        is_metro=False,
    )
    # Min(15000, 10000, 20000) = 10000
    assert r.exempt_monthly == pytest.approx(10_000.0)
    assert r.breakdown["applied_min"] == "rent_minus_10pct_basic"


def test_actual_hra_is_binding():
    """Low HRA limit binds the exemption."""
    r = hra_exemption.calculate(
        basic_monthly=50_000,
        hra_received_monthly=5_000,
        rent_paid_monthly=20_000,
        is_metro=True,
    )
    # actual_hra=5000; rent-10%=15000; 50%=25000 → bound by actual_hra
    assert r.exempt_monthly == pytest.approx(5_000.0)
    assert r.breakdown["applied_min"] == "actual_hra"


def test_zero_rent_yields_zero_exempt():
    """No rent paid → second limb is negative → exempt = 0."""
    r = hra_exemption.calculate(
        basic_monthly=50_000,
        hra_received_monthly=20_000,
        rent_paid_monthly=0,
        is_metro=True,
    )
    assert r.exempt_monthly == 0.0
    # Whole HRA is taxable
    assert r.taxable_hra_annual == pytest.approx(20_000 * 12)


def test_negative_basic_raises():
    with pytest.raises(ValueError, match="basic_monthly"):
        hra_exemption.calculate(-1, 1000, 1000, True)
