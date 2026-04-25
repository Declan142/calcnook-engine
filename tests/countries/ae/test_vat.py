"""Tests for UAE VAT (5%)."""

import pytest

from calcnook.countries.ae import vat


def test_exclusive_1000():
    r = vat.calculate(1000, is_inclusive=False)
    assert r.vat_amount == pytest.approx(50.0)
    assert r.net_amount == 1000.0
    assert r.gross_amount == pytest.approx(1050.0)
    assert r.rate == 0.05
    assert r.is_inclusive is False


def test_inclusive_1050():
    r = vat.calculate(1050, is_inclusive=True)
    assert round(r.vat_amount, 4) == pytest.approx(50.0, abs=0.01)
    assert round(r.net_amount, 4) == pytest.approx(1000.0, abs=0.01)
    assert r.gross_amount == 1050.0
    assert r.is_inclusive is True


def test_zero_amount():
    r = vat.calculate(0)
    assert r.vat_amount == 0.0
    assert r.gross_amount == 0.0


def test_to_dict():
    r = vat.calculate(500)
    d = r.to_dict()
    assert "vat_amount" in d
    assert "net_amount" in d
    assert "gross_amount" in d
    assert d["rate"] == 0.05


def test_negative_amount():
    with pytest.raises(ValueError, match="amount"):
        vat.calculate(-100)
