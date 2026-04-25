"""Tests for Saudi citizen Zakat estimator."""

import pytest

from calcnook.countries.sa import zakat_citizen


def test_basic_2_5_percent():
    r = zakat_citizen.calculate(1_000_000)
    assert r.zakat_due == pytest.approx(25_000.0)


def test_zero_base():
    r = zakat_citizen.calculate(0)
    assert r.zakat_due == 0.0


def test_rate_is_2_5():
    r = zakat_citizen.calculate(500_000)
    assert r.rate == 0.025
    assert r.zakat_due == pytest.approx(12_500.0)


def test_disclaimer_present():
    r = zakat_citizen.calculate(100_000)
    assert "ZATCA" in r.disclaimer
    assert "SIMPLIFIED" in r.disclaimer


def test_to_dict():
    r = zakat_citizen.calculate(400_000)
    d = r.to_dict()
    assert "zakat_due" in d
    assert "zakat_base" in d
    assert "disclaimer" in d


def test_negative_base():
    with pytest.raises(ValueError, match="zakat_base"):
        zakat_citizen.calculate(-1)
