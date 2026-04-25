"""Tests for Saudi Arabia End of Service Gratuity.

Matrix: 4 service lengths × 2 end reasons = 8 core cases.
"""

import pytest

from calcnook.countries.sa import end_of_service_gratuity as eosg


# ---------------------------------------------------------------------------
# Termination (full entitlement)
# ---------------------------------------------------------------------------

def test_termination_3y():
    # 3y (< 5y): 3 * (5000/2) = 7500
    r = eosg.calculate(5_000, 3, "termination")
    assert round(r.gratuity_sar, 2) == pytest.approx(7_500.0)
    assert r.entitlement_factor == 1.0


def test_termination_5y():
    # Exactly 5y: 5 * (5000/2) = 12500
    r = eosg.calculate(5_000, 5, "termination")
    assert round(r.gratuity_sar, 2) == pytest.approx(12_500.0)


def test_termination_8y():
    # 8y: first 5: 5*(5000/2)=12500; next 3: 3*5000=15000; total = 27500
    r = eosg.calculate(5_000, 8, "termination")
    assert round(r.gratuity_sar, 2) == pytest.approx(27_500.0)


def test_termination_12y():
    # 12y: first 5: 12500; next 7: 7*5000=35000; total = 47500
    r = eosg.calculate(5_000, 12, "termination")
    assert round(r.gratuity_sar, 2) == pytest.approx(47_500.0)


# ---------------------------------------------------------------------------
# Resignation (modified entitlement)
# ---------------------------------------------------------------------------

def test_resignation_under_2y_no_gratuity():
    r = eosg.calculate(5_000, 1.5, "resignation")
    assert r.gratuity_sar == 0.0
    assert r.entitlement_factor == 0.0


def test_resignation_3y_one_third():
    # Accrued (3y): 7500; one-third = 2500
    r = eosg.calculate(5_000, 3, "resignation")
    assert round(r.gratuity_sar, 2) == pytest.approx(2_500.0)
    assert round(r.entitlement_factor, 6) == pytest.approx(1 / 3, rel=1e-5)


def test_resignation_7y_two_thirds():
    # Accrued (7y): 12500 + 2*5000 = 22500; two-thirds = 15000
    r = eosg.calculate(5_000, 7, "resignation")
    assert round(r.gratuity_sar, 2) == pytest.approx(15_000.0, abs=1.0)
    assert round(r.entitlement_factor, 6) == pytest.approx(2 / 3, rel=1e-5)


def test_resignation_10y_full():
    # 10y: 12500 + 5*5000=37500; full factor = 37500
    r = eosg.calculate(5_000, 10, "resignation")
    assert round(r.gratuity_sar, 2) == pytest.approx(37_500.0)
    assert r.entitlement_factor == 1.0


def test_to_dict():
    r = eosg.calculate(5_000, 5, "termination")
    d = r.to_dict()
    assert "gratuity_sar" in d
    assert "entitlement_factor" in d
    assert "formula_note" in d


def test_invalid_end_reason():
    with pytest.raises(ValueError, match="end_reason"):
        eosg.calculate(5_000, 5, "quit")


def test_negative_salary():
    with pytest.raises(ValueError, match="monthly_basic_salary"):
        eosg.calculate(-100, 5)
