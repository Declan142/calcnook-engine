"""Saudi Arabia End of Service Gratuity (EOSG) calculator.

Based on Articles 84–87 of the Saudi Labour Law (Royal Decree No. M/51 of 2005,
as amended).

Gratuity accrual:
    - First 5 years: ½ month's basic salary per year
    - After 5 years: 1 full month's basic salary per year

Entitlement modifiers by end_reason:
    - "termination" (by employer): 100% of accrued gratuity
    - "resignation":
        <2 years:   0% (no entitlement)
        2–5 years:  1/3 of accrued gratuity
        5–10 years: 2/3 of accrued gratuity
        10+ years:  100% of accrued gratuity
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_END_REASONS = frozenset({"termination", "resignation"})


@dataclass(frozen=True)
class SAGratuityResult:
    """Result of a Saudi EOSG calculation."""
    monthly_basic_salary: float
    years_of_service: float
    end_reason: str
    accrued_gratuity_full: float    # 100% entitlement before modifier
    entitlement_factor: float       # 0, 1/3, 2/3, or 1.0
    gratuity_sar: float             # final payable amount
    formula_note: str

    def to_dict(self) -> dict:
        return {
            "monthly_basic_salary": round(self.monthly_basic_salary, 2),
            "years_of_service": round(self.years_of_service, 4),
            "end_reason": self.end_reason,
            "accrued_gratuity_full": round(self.accrued_gratuity_full, 2),
            "entitlement_factor": round(self.entitlement_factor, 6),
            "gratuity_sar": round(self.gratuity_sar, 2),
            "formula_note": self.formula_note,
        }


def calculate(
    monthly_basic_salary: float,
    years_of_service: float,
    end_reason: str = "termination",
) -> SAGratuityResult:
    """Compute Saudi Arabia EOSG under Articles 84-87 of the Saudi Labour Law.

    Full accrual formula:
        first_5_gratuity = min(years, 5) * (monthly_basic_salary / 2)
        beyond_5_gratuity = max(0, years - 5) * monthly_basic_salary
        accrued_full = first_5_gratuity + beyond_5_gratuity

    Resignation entitlement factor:
        <2y  → 0.0 (no gratuity)
        2-5y → 1/3
        5-10y → 2/3
        10y+ → 1.0

    Termination (by employer) entitlement factor: always 1.0.

    Args:
        monthly_basic_salary: Monthly basic salary in SAR.
        years_of_service: Total years of service (fractional years accepted).
        end_reason: "termination" (employer-initiated) or "resignation".

    Returns:
        SAGratuityResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(5_000, 3, "resignation")
        >>> round(r.gratuity_sar, 2)
        2500.0
    """
    if monthly_basic_salary < 0:
        raise ValueError("monthly_basic_salary must be >= 0")
    if years_of_service < 0:
        raise ValueError("years_of_service must be >= 0")
    if end_reason not in VALID_END_REASONS:
        raise ValueError(f"end_reason must be one of {sorted(VALID_END_REASONS)}, got {end_reason!r}")

    # Full accrual (100% baseline)
    years_first = min(years_of_service, 5.0)
    years_extra = max(0.0, years_of_service - 5.0)

    accrued = (years_first * monthly_basic_salary / 2.0) + (years_extra * monthly_basic_salary)

    # Entitlement factor
    if end_reason == "termination":
        factor = 1.0
        note = "termination_full_entitlement"
    else:
        # Resignation
        if years_of_service < 2.0:
            factor = 0.0
            note = "resignation_under_2_years_no_gratuity"
        elif years_of_service < 5.0:
            factor = 1.0 / 3.0
            note = "resignation_2_to_5_years_one_third"
        elif years_of_service < 10.0:
            factor = 2.0 / 3.0
            note = "resignation_5_to_10_years_two_thirds"
        else:
            factor = 1.0
            note = "resignation_10_plus_years_full"

    gratuity = accrued * factor

    return SAGratuityResult(
        monthly_basic_salary=monthly_basic_salary,
        years_of_service=years_of_service,
        end_reason=end_reason,
        accrued_gratuity_full=accrued,
        entitlement_factor=factor,
        gratuity_sar=gratuity,
        formula_note=note,
    )
