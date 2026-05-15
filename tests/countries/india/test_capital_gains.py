"""Tests for India Capital Gains — Budget 2024 (FY 2024-25 onwards)."""

import pytest

from calcnook.countries.india import capital_gains


def test_equity_listed_ltcg_above_exemption():
    """Equity LTCG: held >12mo, gain over ₹1.25L → 12.5% on excess."""
    r = capital_gains.calculate(
        asset_type="equity_listed",
        purchase_price=200_000,
        sale_price=350_000,
        purchase_date="2022-04-01",
        sale_date="2024-09-01",
    )
    assert r.classification == "LTCG"
    assert r.gain_amount == pytest.approx(150_000.0)
    assert r.exemption_used == pytest.approx(125_000.0)
    assert r.taxable_gain == pytest.approx(25_000.0)
    # 12.5% × 25000 = 3125
    assert r.tax_payable == pytest.approx(3_125.0)
    assert r.applicable_rate == pytest.approx(0.125)


def test_equity_listed_stcg_20pct():
    """Equity STCG (≤12mo): 20% (Budget 2024 raised from 15%)."""
    r = capital_gains.calculate(
        asset_type="equity_listed",
        purchase_price=100_000,
        sale_price=130_000,
        purchase_date="2024-01-01",
        sale_date="2024-09-01",
    )
    assert r.classification == "STCG"
    # 20% × 30000 = 6000
    assert r.tax_payable == pytest.approx(6_000.0)


def test_debt_mf_slab_rate():
    """Debt MF: always slab rate (Sec 50AA), tax_payable=None."""
    r = capital_gains.calculate(
        asset_type="debt_mf",
        purchase_price=500_000,
        sale_price=600_000,
        purchase_date="2023-04-01",
        sale_date="2026-04-01",
    )
    assert r.classification == "SLAB_RATE"
    assert r.tax_payable is None
    assert "marginal slab rate" in (r.note or "")


def test_property_ltcg_no_indexation_default():
    """Property held >24mo, no indexation → 12.5%."""
    r = capital_gains.calculate(
        asset_type="property",
        purchase_price=5_000_000,
        sale_price=8_000_000,
        purchase_date="2020-01-01",
        sale_date="2025-01-01",
    )
    assert r.classification == "LTCG"
    assert r.indexation_used is False
    assert r.applicable_rate == pytest.approx(0.125)
    # 12.5% × 30L = 3.75L
    assert r.tax_payable == pytest.approx(375_000.0)


def test_property_ltcg_with_indexation_opt_in():
    """Property LTCG with indexation: 20%."""
    r = capital_gains.calculate(
        asset_type="property",
        purchase_price=5_000_000,
        sale_price=8_000_000,
        purchase_date="2020-01-01",
        sale_date="2025-01-01",
        indexation=True,
    )
    assert r.indexation_used is True
    assert r.applicable_rate == pytest.approx(0.20)
    # 20% × 30L = 6L
    assert r.tax_payable == pytest.approx(600_000.0)


def test_unlisted_equity_ltcg():
    """Unlisted equity LTCG (>24mo): 12.5%."""
    r = capital_gains.calculate(
        asset_type="unlisted_equity",
        purchase_price=1_000_000,
        sale_price=2_000_000,
        purchase_date="2022-01-01",
        sale_date="2025-01-01",
    )
    assert r.classification == "LTCG"
    assert r.tax_payable == pytest.approx(125_000.0)


def test_gold_ltcg_no_indexation():
    """Gold held >36mo, no indexation → 12.5%."""
    r = capital_gains.calculate(
        asset_type="gold",
        purchase_price=500_000,
        sale_price=800_000,
        purchase_date="2020-01-01",
        sale_date="2025-01-01",
    )
    assert r.classification == "LTCG"
    assert r.tax_payable == pytest.approx(37_500.0)


def test_crypto_flat_30():
    """Crypto: flat 30% regardless of holding."""
    r = capital_gains.calculate(
        asset_type="crypto",
        purchase_price=100_000,
        sale_price=200_000,
        purchase_date="2024-01-01",
        sale_date="2024-12-01",
    )
    assert r.classification == "FLAT_30"
    assert r.tax_payable == pytest.approx(30_000.0)
    assert r.applicable_rate == pytest.approx(0.30)


def test_loss_returns_zero_tax():
    """Capital loss → 0 tax."""
    r = capital_gains.calculate(
        asset_type="equity_listed",
        purchase_price=200_000,
        sale_price=150_000,
        purchase_date="2022-01-01",
        sale_date="2025-01-01",
    )
    assert r.gain_amount < 0
    assert r.tax_payable == 0.0


def test_invalid_asset_type():
    with pytest.raises(ValueError, match="asset_type"):
        capital_gains.calculate(
            asset_type="bond",
            purchase_price=100,
            sale_price=200,
            purchase_date="2020-01-01",
            sale_date="2024-01-01",
        )


def test_invalid_date_string():
    with pytest.raises(ValueError, match="purchase_date"):
        capital_gains.calculate(
            asset_type="equity_listed",
            purchase_price=100,
            sale_price=200,
            purchase_date="01-01-2020",
            sale_date="2024-01-01",
        )
