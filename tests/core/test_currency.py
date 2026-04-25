"""Tests for currency conversion, formatting, and lakh/crore notation."""

import pytest

from calcnook.core import currency


SAMPLE_RATES = {
    "USD": 1.0,
    "INR": 83.5,
    "EUR": 0.93,
    "GBP": 0.79,
    "AED": 3.67,
    "JPY": 155.0,
}


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------

def test_usd_to_inr():
    result = currency.convert(1000, "USD", "INR", SAMPLE_RATES)
    assert result.converted_amount == pytest.approx(83_500.0, rel=1e-6)


def test_inr_to_usd():
    result = currency.convert(83_500, "INR", "USD", SAMPLE_RATES)
    assert result.converted_amount == pytest.approx(1000.0, rel=1e-4)


def test_roundtrip_usd_eur_usd():
    mid = currency.convert(100, "USD", "EUR", SAMPLE_RATES)
    back = currency.convert(mid.converted_amount, "EUR", "USD", SAMPLE_RATES)
    assert back.converted_amount == pytest.approx(100.0, rel=1e-4)


def test_same_currency_converts_equal():
    result = currency.convert(500, "USD", "USD", SAMPLE_RATES)
    assert result.converted_amount == pytest.approx(500.0, rel=1e-9)


def test_zero_amount():
    result = currency.convert(0, "USD", "INR", SAMPLE_RATES)
    assert result.converted_amount == 0.0


def test_cross_currency_aed_gbp():
    # AED → USD → GBP
    result = currency.convert(3.67, "AED", "GBP", SAMPLE_RATES)
    expected = (3.67 / 3.67) * 0.79
    assert result.converted_amount == pytest.approx(expected, rel=1e-6)


def test_missing_from_currency_raises():
    with pytest.raises(ValueError, match="CHF"):
        currency.convert(100, "CHF", "USD", SAMPLE_RATES)


def test_missing_to_currency_raises():
    with pytest.raises(ValueError, match="SAR"):
        currency.convert(100, "USD", "SAR", SAMPLE_RATES)


def test_negative_amount_raises():
    with pytest.raises(ValueError, match="amount"):
        currency.convert(-100, "USD", "INR", SAMPLE_RATES)


def test_to_dict_keys():
    result = currency.convert(1000, "USD", "INR", SAMPLE_RATES)
    d = result.to_dict()
    for key in ("amount", "from_currency", "to_currency", "rate_used", "converted_amount"):
        assert key in d


# ---------------------------------------------------------------------------
# format_amount
# ---------------------------------------------------------------------------

def test_format_usd():
    assert currency.format_amount(1234.56, "USD") == "$1,234.56"


def test_format_inr():
    assert currency.format_amount(83500.0, "INR") == "₹83,500.00"


def test_format_eur():
    assert currency.format_amount(999.99, "EUR") == "€999.99"


def test_format_gbp():
    assert currency.format_amount(500.0, "GBP") == "£500.00"


def test_format_jpy_no_decimals():
    assert currency.format_amount(1500, "JPY") == "¥1,500"


def test_format_cny_no_decimals():
    assert currency.format_amount(2000, "CNY") == "¥2,000"


def test_format_aed():
    result = currency.format_amount(100.0, "AED")
    assert "100.00" in result
    assert "AED" in result


def test_format_unknown_currency():
    result = currency.format_amount(100.0, "XYZ")
    assert "XYZ" in result
    assert "100.00" in result


# ---------------------------------------------------------------------------
# lakh_crore_format
# ---------------------------------------------------------------------------

def test_lakh_format_1_5L():
    assert currency.lakh_crore_format(150_000) == "₹1.50 L"


def test_crore_format_2_5cr():
    assert currency.lakh_crore_format(25_000_000) == "₹2.50 Cr"


def test_crore_format_1cr():
    assert currency.lakh_crore_format(10_000_000) == "₹1.00 Cr"


def test_lakh_boundary():
    # Exactly 1 lakh
    assert currency.lakh_crore_format(100_000) == "₹1.00 L"


def test_crore_boundary():
    # Exactly 1 crore
    assert currency.lakh_crore_format(10_000_000) == "₹1.00 Cr"


def test_below_lakh():
    result = currency.lakh_crore_format(50_000)
    assert result == "₹50,000.00"
    assert "L" not in result
    assert "Cr" not in result


def test_zero_amount():
    result = currency.lakh_crore_format(0)
    assert result == "₹0.00"


def test_negative_amount_raises():
    with pytest.raises(ValueError, match="amount"):
        currency.lakh_crore_format(-100)


def test_large_crore():
    # 100 Cr
    assert currency.lakh_crore_format(1_000_000_000) == "₹100.00 Cr"
