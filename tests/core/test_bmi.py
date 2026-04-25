"""Tests for BMI, BMR, and TDEE calculations."""

import pytest

from calcnook.core import bmi as bmi_module


# ---------------------------------------------------------------------------
# BMI
# ---------------------------------------------------------------------------

def test_bmi_normal():
    result = bmi_module.bmi(70, 175)
    # 70 / (1.75^2) = 70 / 3.0625 = 22.857...
    assert result.bmi == pytest.approx(22.857, rel=1e-3)
    assert result.category == "normal"


def test_bmi_underweight():
    # 45 kg, 175 cm -> 45/3.0625 = 14.69
    result = bmi_module.bmi(45, 175)
    assert result.category == "underweight"


def test_bmi_overweight():
    # 85 kg, 170 cm -> 85/2.89 = 29.41
    result = bmi_module.bmi(85, 170)
    assert result.category == "overweight"


def test_bmi_obese():
    # 120 kg, 170 cm -> 120/2.89 = 41.52
    result = bmi_module.bmi(120, 170)
    assert result.category == "obese"


def test_bmi_boundary_normal_25():
    # Exactly 25.0 -> overweight
    # Need weight such that w / h^2 = 25 -> w = 25 * 1.75^2 = 76.5625
    result = bmi_module.bmi(76.5625, 175)
    assert result.category == "overweight"


def test_bmi_boundary_underweight_18_5():
    # Exactly 18.5 -> normal
    # weight = 18.5 * 1.75^2 = 56.65625
    result = bmi_module.bmi(56.65625, 175)
    assert result.category == "normal"


def test_bmi_invalid_weight():
    with pytest.raises(ValueError, match="weight_kg"):
        bmi_module.bmi(0, 175)


def test_bmi_invalid_height():
    with pytest.raises(ValueError, match="height_cm"):
        bmi_module.bmi(70, -10)


def test_bmi_to_dict():
    result = bmi_module.bmi(70, 175)
    d = result.to_dict()
    assert "bmi" in d
    assert "category" in d
    assert d["weight_kg"] == 70
    assert d["height_cm"] == 175


# ---------------------------------------------------------------------------
# BMR
# ---------------------------------------------------------------------------

def test_bmr_male_reference():
    # 70kg, 175cm, 30y, male
    # BMR = 10*70 + 6.25*175 - 5*30 + 5 = 700 + 1093.75 - 150 + 5 = 1648.75
    result = bmi_module.bmr(70, 175, 30, "male")
    assert result.bmr_kcal == pytest.approx(1648.75, rel=1e-6)


def test_bmr_female_reference():
    # 60kg, 165cm, 25y, female
    # BMR = 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
    result = bmi_module.bmr(60, 165, 25, "female")
    assert result.bmr_kcal == pytest.approx(1345.25, rel=1e-6)


def test_bmr_male_vs_female_same_stats():
    # Male always higher by 5 + 161 = 166 kcal for same stats
    m = bmi_module.bmr(70, 175, 30, "male")
    f = bmi_module.bmr(70, 175, 30, "female")
    assert m.bmr_kcal - f.bmr_kcal == pytest.approx(166.0, rel=1e-6)


def test_bmr_invalid_sex():
    with pytest.raises(ValueError, match="sex"):
        bmi_module.bmr(70, 175, 30, "other")


def test_bmr_invalid_age():
    with pytest.raises(ValueError, match="age_years"):
        bmi_module.bmr(70, 175, 0, "male")


def test_bmr_invalid_weight():
    with pytest.raises(ValueError, match="weight_kg"):
        bmi_module.bmr(-10, 175, 30, "male")


def test_bmr_to_dict():
    result = bmi_module.bmr(70, 175, 30, "male")
    d = result.to_dict()
    assert "bmr_kcal" in d
    assert d["sex"] == "male"


# ---------------------------------------------------------------------------
# TDEE
# ---------------------------------------------------------------------------

def test_tdee_sedentary():
    result = bmi_module.tdee(1648.75, "sedentary")
    assert result.tdee_kcal == pytest.approx(1648.75 * 1.2, rel=1e-6)


def test_tdee_moderate():
    result = bmi_module.tdee(1648.75, "moderate")
    assert result.tdee_kcal == pytest.approx(1648.75 * 1.55, rel=1e-6)


def test_tdee_very_active():
    result = bmi_module.tdee(2000, "very_active")
    assert result.tdee_kcal == pytest.approx(2000 * 1.9, rel=1e-6)


def test_tdee_all_levels():
    levels = ["sedentary", "light", "moderate", "active", "very_active"]
    for level in levels:
        r = bmi_module.tdee(1500, level)
        assert r.tdee_kcal > 1500


def test_tdee_invalid_level():
    with pytest.raises(ValueError, match="activity_level"):
        bmi_module.tdee(1500, "super_athlete")


def test_tdee_invalid_bmr():
    with pytest.raises(ValueError, match="bmr_kcal"):
        bmi_module.tdee(0, "sedentary")


def test_tdee_to_dict():
    result = bmi_module.tdee(1648.75, "moderate")
    d = result.to_dict()
    assert "tdee_kcal" in d
    assert "activity_level" in d
    assert "activity_multiplier" in d
    assert d["activity_multiplier"] == 1.55
