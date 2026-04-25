"""Tests for India electricity bill slab-tariff calculator."""

import pytest

from calcnook.countries.india import electricity_bill
from calcnook.countries.india.electricity_bill import (
    BESCOM_RESIDENTIAL,
    MSEB_RESIDENTIAL,
    BSES_RESIDENTIAL,
)


def test_bescom_150_units():
    # BESCOM: 0-30 free, 31-100 @ 4.10, 101-200 @ 5.55
    # 30 units free (0); 70 units @ 4.10 = 287; 50 units @ 5.55 = 277.5
    # energy = 0 + 287 + 277.5 = 564.5
    r = electricity_bill.calculate(150, BESCOM_RESIDENTIAL)
    assert round(r.energy_charge, 2) == pytest.approx(564.5, abs=1.0)
    assert r.units_consumed == 150.0


def test_bescom_with_fixed_charge():
    r = electricity_bill.calculate(100, BESCOM_RESIDENTIAL, fixed_charges=50)
    # 30 free + 70 @ 4.10 = 287; fixed = 50 → total = 337
    assert round(r.total_bill, 2) == pytest.approx(337.0, abs=1.0)


def test_surcharge_applied():
    r = electricity_bill.calculate(
        200, MSEB_RESIDENTIAL,
        fuel_surcharge_per_unit=0.50
    )
    assert round(r.fuel_surcharge, 2) == pytest.approx(100.0)  # 200 * 0.50


def test_electricity_duty():
    r = electricity_bill.calculate(
        100, BSES_RESIDENTIAL,
        electricity_duty_percent=5.0
    )
    # energy = 100 * 3.00 = 300; duty = 300 * 5% = 15
    assert round(r.electricity_duty, 2) == pytest.approx(15.0, abs=0.5)
    assert round(r.total_bill, 2) == pytest.approx(315.0, abs=1.0)


def test_zero_units():
    r = electricity_bill.calculate(0, BESCOM_RESIDENTIAL)
    assert r.energy_charge == 0.0
    assert r.total_bill == 0.0


def test_custom_slabs():
    slabs = [(100, 2.0), (300, 3.5), (float("inf"), 5.0)]
    # 50 units all in first slab: 50 * 2.0 = 100
    r = electricity_bill.calculate(50, slabs)
    assert round(r.energy_charge, 2) == pytest.approx(100.0)


def test_custom_slabs_cross_boundary():
    slabs = [(100, 2.0), (float("inf"), 4.0)]
    # 150 units: 100 * 2 + 50 * 4 = 200 + 200 = 400
    r = electricity_bill.calculate(150, slabs)
    assert round(r.energy_charge, 2) == pytest.approx(400.0)


def test_to_dict():
    r = electricity_bill.calculate(100, BESCOM_RESIDENTIAL)
    d = r.to_dict()
    assert "energy_charge" in d
    assert "total_bill" in d
    assert "slab_breakdown" in d
    assert isinstance(d["slab_breakdown"], list)


def test_negative_units():
    with pytest.raises(ValueError, match="units_consumed"):
        electricity_bill.calculate(-1, BESCOM_RESIDENTIAL)


def test_empty_slabs():
    with pytest.raises(ValueError, match="slabs"):
        electricity_bill.calculate(100, [])


def test_mseb_100_units():
    # MSEB: first 100 @ 3.78 = 378
    r = electricity_bill.calculate(100, MSEB_RESIDENTIAL)
    assert round(r.energy_charge, 2) == pytest.approx(378.0, abs=1.0)
