"""India Gratuity calculator — Payment of Gratuity Act, 1972.

Statutory backing:
    - Section 4 of the Payment of Gratuity Act, 1972.
    - Section 10(10)(ii) of the Income-tax Act, 1961 (exemption cap ₹20,00,000).

Formula (private-sector employees covered by the Act):
    gratuity = (15 × (basic + DA) × years_of_service) / 26

The factor 15/26 represents 15 days of last-drawn wage per completed year of
service, with a 26-day working month (per Section 4(2)).

Years of service convention:
    - Years are floored to a whole integer ONLY for the count below the
      6-month threshold. Per Section 4(2), service exceeding 6 months in the
      final year counts as one full year — but the user spec for this engine
      asks for floor() of years_of_service, so we follow the spec strictly.
    - Service less than 5 years (continuous service) generally disqualifies the
      employee under Section 4(1), but that eligibility check is left to the
      caller — we still compute the formula for any years >= 0.

Tax exemption:
    - Section 10(10)(ii): non-government employees covered under the Act may
      claim the LEAST of (gratuity received, statutory formula amount, ₹20L)
      as exempt. This calculator computes the formula amount and applies the
      ₹20L cap; the "least of three" check is left to the caller's full ITR
      logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


WORKING_DAYS_DENOMINATOR = 26.0
DAYS_PER_YEAR_FACTOR = 15.0
EXEMPT_CAP = 2_000_000.0  # ₹20,00,000 per Sec 10(10)(ii)


@dataclass(frozen=True)
class GratuityResult:
    """Result of a Payment-of-Gratuity-Act calculation."""
    monthly_basic_salary: float
    dearness_allowance: float
    years_of_service_input: float
    years_of_service_used: int
    gratuity_gross: float
    exempt_amount: float
    taxable_amount: float
    formula_breakdown: dict

    def to_dict(self) -> dict:
        return {
            "monthly_basic_salary": round(self.monthly_basic_salary, 2),
            "dearness_allowance": round(self.dearness_allowance, 2),
            "years_of_service_input": self.years_of_service_input,
            "years_of_service_used": self.years_of_service_used,
            "gratuity_gross": round(self.gratuity_gross, 2),
            "exempt_amount": round(self.exempt_amount, 2),
            "taxable_amount": round(self.taxable_amount, 2),
            "formula_breakdown": self.formula_breakdown,
        }


def calculate(
    monthly_basic_salary: float,
    years_of_service: float,
    dearness_allowance: float = 0.0,
) -> GratuityResult:
    """Compute statutory gratuity under the Payment of Gratuity Act, 1972.

    Formula::

        gratuity = (15 × (basic + DA) × floor(years_of_service)) / 26

    Tax-exempt portion is the lesser of computed gratuity and ₹20,00,000 per
    Section 10(10)(ii) of the Income-tax Act.

    Args:
        monthly_basic_salary: Last-drawn monthly basic salary in INR.
        years_of_service: Total years of continuous service (any float).
            Floored to int for the formula, per the engine spec for this
            module. Service of 7.5 years → 7 years used.
        dearness_allowance: Last-drawn dearness allowance in INR per month.
            Added to basic for the (basic + DA) term.

    Returns:
        GratuityResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(monthly_basic_salary=50_000, years_of_service=10)
        >>> r.gratuity_gross   # (15 × 50000 × 10) / 26
        288461.54
    """
    if monthly_basic_salary < 0:
        raise ValueError("monthly_basic_salary must be >= 0")
    if years_of_service < 0:
        raise ValueError("years_of_service must be >= 0")
    if dearness_allowance < 0:
        raise ValueError("dearness_allowance must be >= 0")

    years_used = int(math.floor(years_of_service))
    monthly_wage = monthly_basic_salary + dearness_allowance

    gratuity_gross = (DAYS_PER_YEAR_FACTOR * monthly_wage * years_used) / WORKING_DAYS_DENOMINATOR

    exempt = min(gratuity_gross, EXEMPT_CAP)
    taxable = max(0.0, gratuity_gross - exempt)

    breakdown = {
        "formula": "(15 × (basic + DA) × floor(years_of_service)) / 26",
        "monthly_wage_basic_plus_da": round(monthly_wage, 2),
        "days_per_year_factor": DAYS_PER_YEAR_FACTOR,
        "working_days_denominator": WORKING_DAYS_DENOMINATOR,
        "exempt_cap": EXEMPT_CAP,
        "exempt_cap_basis": "Section 10(10)(ii) Income-tax Act, 1961",
    }

    return GratuityResult(
        monthly_basic_salary=monthly_basic_salary,
        dearness_allowance=dearness_allowance,
        years_of_service_input=years_of_service,
        years_of_service_used=years_used,
        gratuity_gross=gratuity_gross,
        exempt_amount=exempt,
        taxable_amount=taxable,
        formula_breakdown=breakdown,
    )
