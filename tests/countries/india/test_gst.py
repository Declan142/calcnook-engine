"""Tests for India GST — CGST/SGST/IGST."""

import pytest

from calcnook.countries.india import gst


def test_5pct_intra_state_exclusive():
    r = gst.calculate(amount=1000, rate=5, breakup="cgst_sgst")
    assert r.gst_total == pytest.approx(50.0)
    assert r.cgst == pytest.approx(25.0)
    assert r.sgst == pytest.approx(25.0)
    assert r.igst == 0.0
    assert r.total == pytest.approx(1050.0)


def test_12pct_inter_state_igst():
    r = gst.calculate(amount=1000, rate=12, breakup="igst")
    assert r.igst == pytest.approx(120.0)
    assert r.cgst == 0.0
    assert r.sgst == 0.0
    assert r.total == pytest.approx(1120.0)


def test_18pct_intra_state_inclusive_extracts_base():
    """₹1180 inclusive of 18% GST → base = 1000."""
    r = gst.calculate(amount=1180, rate=18, is_inclusive=True, breakup="cgst_sgst")
    assert r.base == pytest.approx(1000.0, rel=1e-4)
    assert r.gst_total == pytest.approx(180.0, rel=1e-4)
    assert r.cgst == pytest.approx(90.0, rel=1e-4)
    assert r.sgst == pytest.approx(90.0, rel=1e-4)


def test_28pct_decimal_rate_input():
    """Rate as decimal 0.28 should be auto-detected."""
    r = gst.calculate(amount=1000, rate=0.28)
    assert r.rate_pct == pytest.approx(28.0)
    assert r.gst_total == pytest.approx(280.0)


def test_zero_rate():
    r = gst.calculate(amount=1000, rate=0)
    assert r.gst_total == 0.0
    assert r.total == pytest.approx(1000.0)


def test_invalid_rate_rejected():
    with pytest.raises(ValueError, match="not in permitted slabs"):
        gst.calculate(amount=1000, rate=10)


def test_invalid_breakup_rejected():
    with pytest.raises(ValueError, match="breakup"):
        gst.calculate(amount=1000, rate=18, breakup="state_only")
