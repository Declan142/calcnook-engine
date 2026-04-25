"""UAE End of Service Gratuity (EOSG) calculator.

Based on Article 51 of UAE Labour Law (Federal Decree-Law No. 33 of 2021).
Since February 2022 all new employment contracts are "limited-term" under the
new federal system. The classic "unlimited-term" distinction applies to pre-2022
legacy contracts only.

Formula:
    - First 5 years: 21 working days of basic salary per year
    - After 5 years: 30 working days of basic salary per year
    - Cap: total gratuity ≤ 2 years' basic salary

Working-days basis: 1 month = 30 calendar days (Labour Law standard).
"""

from __future__ import annotations

from dataclasses import dataclass


DAYS_PER_MONTH = 30.0
RATE_FIRST_5_YEARS = 21.0    # working days per year, years 1-5
RATE_AFTER_5_YEARS = 30.0    # working days per year, year 6+
MAX_GRATUITY_MONTHS = 24.0   # cap = 2 years' basic salary


@dataclass(frozen=True)
class AEGratuityResult:
    """Result of a UAE EOSG calculation."""
    monthly_basic_salary: float
    years_of_service: float
    daily_basic_wage: float
    gratuity_before_cap: float
    gratuity_aed: float
    is_capped: bool
    formula_used: str

    def to_dict(self) -> dict:
        return {
            "monthly_basic_salary": round(self.monthly_basic_salary, 2),
            "years_of_service": round(self.years_of_service, 4),
            "daily_basic_wage": round(self.daily_basic_wage, 4),
            "gratuity_before_cap": round(self.gratuity_before_cap, 2),
            "gratuity_aed": round(self.gratuity_aed, 2),
            "is_capped": self.is_capped,
            "formula_used": self.formula_used,
        }


def calculate(
    monthly_basic_salary: float,
    years_of_service: float,
    contract_type: str = "limited",
) -> AEGratuityResult:
    """Compute UAE End of Service Gratuity under Federal Decree-Law 33/2021.

    For service less than 1 year, no gratuity is payable (returns 0).
    For exactly or more than 1 year, the formula applies on a pro-rata basis
    for partial years.

    Since February 2022 all contracts are limited-term. The ``contract_type``
    parameter is retained for API compatibility with legacy systems but the
    formula is identical for both types under Decree-Law 33/2021.

    Calculation:
        daily_basic_wage = monthly_basic_salary / 30
        first_5_gratuity = min(years, 5) * 21 * daily_basic_wage
        beyond_5_gratuity = max(0, years - 5) * 30 * daily_basic_wage
        total = first_5_gratuity + beyond_5_gratuity
        cap = 24 * monthly_basic_salary
        gratuity = min(total, cap)

    Args:
        monthly_basic_salary: Monthly basic salary in AED (excludes allowances).
        years_of_service: Total years of service (fractional years accepted).
        contract_type: "limited" or "unlimited" — both compute identically under
            the 2021 Decree-Law. Accepted for backwards compatibility.

    Returns:
        AEGratuityResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(8_000, 5)
        >>> round(r.gratuity_aed, 2)
        28000.0
    """
    if monthly_basic_salary < 0:
        raise ValueError("monthly_basic_salary must be >= 0")
    if years_of_service < 0:
        raise ValueError("years_of_service must be >= 0")
    if contract_type not in {"limited", "unlimited"}:
        raise ValueError("contract_type must be 'limited' or 'unlimited'")

    # Less than 1 full year — no gratuity
    if years_of_service < 1.0:
        daily_wage = monthly_basic_salary / DAYS_PER_MONTH
        return AEGratuityResult(
            monthly_basic_salary=monthly_basic_salary,
            years_of_service=years_of_service,
            daily_basic_wage=daily_wage,
            gratuity_before_cap=0.0,
            gratuity_aed=0.0,
            is_capped=False,
            formula_used="no_gratuity_under_1_year",
        )

    daily_wage = monthly_basic_salary / DAYS_PER_MONTH

    years_first = min(years_of_service, 5.0)
    years_extra = max(0.0, years_of_service - 5.0)

    gratuity_first = years_first * RATE_FIRST_5_YEARS * daily_wage
    gratuity_extra = years_extra * RATE_AFTER_5_YEARS * daily_wage
    gratuity_raw = gratuity_first + gratuity_extra

    cap = MAX_GRATUITY_MONTHS * monthly_basic_salary
    gratuity_final = min(gratuity_raw, cap)
    is_capped = gratuity_raw > cap

    formula = "21_days_per_year_first_5_then_30_days"

    return AEGratuityResult(
        monthly_basic_salary=monthly_basic_salary,
        years_of_service=years_of_service,
        daily_basic_wage=daily_wage,
        gratuity_before_cap=gratuity_raw,
        gratuity_aed=gratuity_final,
        is_capped=is_capped,
        formula_used=formula,
    )
