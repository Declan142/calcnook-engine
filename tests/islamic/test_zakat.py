"""Tests for zakat (Islamic wealth obligation)."""

import pytest

from calcnook.core.islamic import zakat


def test_above_silver_nisab_simple():
    # 10k cash + 15k stocks - 2k debts = 23k net wealth
    # silver nisab: 595g * 0.90 = 535.5 USD
    # 23k > 535.5 → zakat due = 23k * 2.5% = 575
    r = zakat.calculate(
        cash=10_000, stocks_value=15_000, debts=2_000,
        gold_price_per_gram=75, silver_price_per_gram=0.90,
        nisab_basis="silver", currency="USD",
    )
    assert r.is_above_nisab is True
    assert round(r.zakat_due, 2) == 575.00
    assert round(r.total_zakatable_assets, 2) == 23000.00


def test_below_nisab_no_zakat():
    # 100 cash, no other assets, silver nisab is ~535
    r = zakat.calculate(
        cash=100, silver_price_per_gram=0.90, nisab_basis="silver",
    )
    assert r.is_above_nisab is False
    assert r.zakat_due == 0.0


def test_gold_nisab_basis():
    # gold nisab: 85g * 75 = 6375
    # 6000 net is below gold nisab
    r = zakat.calculate(
        cash=6000, gold_price_per_gram=75, silver_price_per_gram=0.90,
        nisab_basis="gold",
    )
    assert r.is_above_nisab is False
    assert r.nisab_basis == "gold"
    assert round(r.nisab_threshold_used, 2) == 6375.00


def test_gold_grams_counted():
    # 200g of gold @ 75 = 15000 USD value
    r = zakat.calculate(
        gold_grams=200, gold_price_per_gram=75, silver_price_per_gram=0.90,
        nisab_basis="silver",
    )
    assert round(r.total_zakatable_assets, 2) == 15000.00
    assert r.is_above_nisab is True
    assert round(r.zakat_due, 2) == 375.00


def test_debts_reduce_wealth():
    # cash 10k, debts 9.5k -> net 500. silver nisab ~535. Below → no zakat.
    r = zakat.calculate(
        cash=10_000, debts=9_500,
        silver_price_per_gram=0.90, nisab_basis="silver",
    )
    assert r.is_above_nisab is False
    assert r.zakat_due == 0.0


def test_all_asset_classes_summed():
    r = zakat.calculate(
        cash=1000, gold_grams=10, silver_grams=100,
        stocks_value=2000, business_assets=500,
        other_zakatable_assets=200, debts=100,
        gold_price_per_gram=75, silver_price_per_gram=0.90,
    )
    expected = 1000 + 750 + 90 + 2000 + 500 + 200 - 100
    assert round(r.total_zakatable_assets, 2) == round(expected, 2)


def test_negative_input_rejected():
    with pytest.raises(ValueError, match="cash"):
        zakat.calculate(cash=-1)


def test_invalid_basis_rejected():
    with pytest.raises(ValueError, match="nisab_basis"):
        zakat.calculate(cash=1000, nisab_basis="bitcoin")


def test_currency_passes_through():
    r = zakat.calculate(cash=100_000, currency="AED")
    assert r.currency == "AED"


def test_to_dict():
    r = zakat.calculate(cash=10_000, debts=2_000)
    d = r.to_dict()
    assert "zakat_due" in d
    assert "is_above_nisab" in d
    assert d["currency"] == "USD"
