"""Tests for compound_interest."""

import pytest

from calcnook.core import compound_interest


def test_basic_growth_monthly():
    r = compound_interest.calculate(10_000, 0.07, 10)
    assert r.compounding_per_year == 12
    assert round(r.future_value, 2) == 20096.61
    assert round(r.interest_earned, 2) == 10096.61


def test_basic_growth_annual():
    # 1000 @ 5% for 3 years compounded annually = 1157.625
    r = compound_interest.calculate(1000, 0.05, 3, compounding_per_year=1)
    assert round(r.future_value, 4) == 1157.6250


def test_basic_growth_quarterly():
    # 5000 @ 6% for 5 years compounded quarterly
    r = compound_interest.calculate(5000, 0.06, 5, compounding_per_year=4)
    expected = 5000 * (1 + 0.06 / 4) ** (4 * 5)
    assert round(r.future_value, 6) == round(expected, 6)


def test_zero_principal():
    r = compound_interest.calculate(0, 0.10, 10)
    assert r.future_value == 0.0
    assert r.interest_earned == 0.0


def test_zero_years():
    r = compound_interest.calculate(1000, 0.10, 0)
    assert r.future_value == 1000.0
    assert r.interest_earned == 0.0


def test_zero_rate():
    r = compound_interest.calculate(1000, 0.0, 10)
    assert r.future_value == 1000.0
    assert r.interest_earned == 0.0


def test_negative_principal_rejected():
    with pytest.raises(ValueError, match="principal"):
        compound_interest.calculate(-1, 0.05, 5)


def test_negative_years_rejected():
    with pytest.raises(ValueError, match="years"):
        compound_interest.calculate(1000, 0.05, -1)


def test_invalid_compounding_rejected():
    with pytest.raises(ValueError, match="compounding_per_year"):
        compound_interest.calculate(1000, 0.05, 5, compounding_per_year=0)


def test_to_dict_roundtrips():
    r = compound_interest.calculate(10_000, 0.07, 10)
    d = r.to_dict()
    assert d["principal"] == 10000.0
    assert d["future_value"] == 20096.61
    assert d["compounding_per_year"] == 12


def test_continuous_via_high_n():
    # As n -> inf, FV -> P * e^(r*t).
    import math
    p, r, t = 10_000, 0.10, 5
    expected = p * math.exp(r * t)
    res = compound_interest.calculate(p, r, t, compounding_per_year=10_000)
    assert abs(res.future_value - expected) / expected < 1e-3
