"""BMI, BMR (Mifflin-St Jeor), and TDEE calculation.

Universal calculation. No country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass

_ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


# ---------------------------------------------------------------------------
# BMI
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BMIResult:
    weight_kg: float
    height_cm: float
    bmi: float
    category: str

    def to_dict(self) -> dict:
        return {
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "bmi": round(self.bmi, 2),
            "category": self.category,
        }


def bmi(weight_kg: float, height_cm: float) -> BMIResult:
    """Compute Body Mass Index and WHO category.

    Formula: BMI = weight_kg / (height_m)^2

    Categories (WHO):
        - Underweight: < 18.5
        - Normal: 18.5 – 24.9
        - Overweight: 25.0 – 29.9
        - Obese: >= 30.0

    Args:
        weight_kg: Body weight in kilograms. Must be > 0.
        height_cm: Height in centimetres. Must be > 0.

    Returns:
        BMIResult with bmi value and category string.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = bmi(70, 175)
        >>> round(r.bmi, 2)
        22.86
        >>> r.category
        'normal'
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if height_cm <= 0:
        raise ValueError("height_cm must be > 0")

    height_m = height_cm / 100
    bmi_value = weight_kg / (height_m ** 2)

    if bmi_value < 18.5:
        category = "underweight"
    elif bmi_value < 25.0:
        category = "normal"
    elif bmi_value < 30.0:
        category = "overweight"
    else:
        category = "obese"

    return BMIResult(
        weight_kg=weight_kg,
        height_cm=height_cm,
        bmi=bmi_value,
        category=category,
    )


# ---------------------------------------------------------------------------
# BMR
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BMRResult:
    weight_kg: float
    height_cm: float
    age_years: int
    sex: str
    bmr_kcal: float

    def to_dict(self) -> dict:
        return {
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "age_years": self.age_years,
            "sex": self.sex,
            "bmr_kcal": round(self.bmr_kcal, 2),
        }


def bmr(
    weight_kg: float,
    height_cm: float,
    age_years: int,
    sex: str,
) -> BMRResult:
    """Compute Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Formula:
        Men:   BMR = 10*W + 6.25*H - 5*A + 5
        Women: BMR = 10*W + 6.25*H - 5*A - 161
    where W = weight_kg, H = height_cm, A = age_years.

    Args:
        weight_kg: Body weight in kilograms. Must be > 0.
        height_cm: Height in centimetres. Must be > 0.
        age_years: Age in whole years. Must be >= 1.
        sex: Biological sex for the equation. Must be "male" or "female".

    Returns:
        BMRResult with bmr_kcal.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = bmr(70, 175, 30, "male")
        >>> round(r.bmr_kcal, 2)
        1673.75
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if height_cm <= 0:
        raise ValueError("height_cm must be > 0")
    if age_years < 1:
        raise ValueError("age_years must be >= 1")
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")

    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    bmr_value = base + 5 if sex == "male" else base - 161

    return BMRResult(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age_years=age_years,
        sex=sex,
        bmr_kcal=bmr_value,
    )


# ---------------------------------------------------------------------------
# TDEE
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TDEEResult:
    bmr_kcal: float
    activity_level: str
    activity_multiplier: float
    tdee_kcal: float

    def to_dict(self) -> dict:
        return {
            "bmr_kcal": round(self.bmr_kcal, 2),
            "activity_level": self.activity_level,
            "activity_multiplier": self.activity_multiplier,
            "tdee_kcal": round(self.tdee_kcal, 2),
        }


def tdee(bmr_kcal: float, activity_level: str) -> TDEEResult:
    """Compute Total Daily Energy Expenditure from BMR and activity level.

    Activity multipliers:
        sedentary   – 1.200 (desk job, no exercise)
        light       – 1.375 (1-3 days/week exercise)
        moderate    – 1.550 (3-5 days/week exercise)
        active      – 1.725 (6-7 days/week hard exercise)
        very_active – 1.900 (physical job + daily hard training)

    Args:
        bmr_kcal: Basal Metabolic Rate in kcal. Must be > 0.
        activity_level: One of {"sedentary", "light", "moderate", "active",
            "very_active"}.

    Returns:
        TDEEResult with tdee_kcal.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = tdee(1673.75, "moderate")
        >>> round(r.tdee_kcal, 2)
        2594.31
    """
    if bmr_kcal <= 0:
        raise ValueError("bmr_kcal must be > 0")
    if activity_level not in _ACTIVITY_MULTIPLIERS:
        raise ValueError(
            f"activity_level must be one of {set(_ACTIVITY_MULTIPLIERS)}"
        )

    multiplier = _ACTIVITY_MULTIPLIERS[activity_level]
    tdee_value = bmr_kcal * multiplier

    return TDEEResult(
        bmr_kcal=bmr_kcal,
        activity_level=activity_level,
        activity_multiplier=multiplier,
        tdee_kcal=tdee_value,
    )
