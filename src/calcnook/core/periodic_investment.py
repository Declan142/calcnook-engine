"""Periodic investment — SIP / DCA with optional annual step-up.

Universal calculation. No country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodicInvestmentResult:
    monthly_amount: float
    annual_return: float
    years: float
    step_up_percent: float
    total_invested: float
    future_value: float
    wealth_gained: float

    def to_dict(self) -> dict:
        return {
            "monthly_amount": round(self.monthly_amount, 2),
            "annual_return": self.annual_return,
            "years": self.years,
            "step_up_percent": self.step_up_percent,
            "total_invested": round(self.total_invested, 2),
            "future_value": round(self.future_value, 2),
            "wealth_gained": round(self.wealth_gained, 2),
        }


def calculate(
    monthly_amount: float,
    annual_return: float,
    years: float,
    step_up_percent: float = 0.0,
) -> PeriodicInvestmentResult:
    """Compute future value of a series of periodic contributions (SIP / DCA).

    For zero step-up, uses the standard SIP formula (ordinary annuity, end-of-period):
        FV = P * ((1+r)^n - 1) / r * (1+r)
    where r = monthly rate, n = total months.

    For step_up > 0, the monthly contribution grows by step_up_percent each year.
    The year-by-year FV is accumulated iteratively.

    Args:
        monthly_amount: Fixed monthly contribution. Must be >= 0.
        annual_return: Decimal annual return, e.g. 0.12 for 12%.
        years: Investment horizon in years. Must be >= 0.
        step_up_percent: Annual percentage increase in monthly contribution.
            e.g. 0.10 means contribution grows 10% each year. Default 0.0.

    Returns:
        PeriodicInvestmentResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(5000, 0.12, 10)
        >>> round(r.future_value, 2)
        1164941.48
    """
    if monthly_amount < 0:
        raise ValueError("monthly_amount must be >= 0")
    if years < 0:
        raise ValueError("years must be >= 0")
    if step_up_percent < 0:
        raise ValueError("step_up_percent must be >= 0")

    monthly_rate = annual_return / 12
    n_months = int(years * 12)

    if n_months == 0 or monthly_amount == 0:
        return PeriodicInvestmentResult(
            monthly_amount=monthly_amount,
            annual_return=annual_return,
            years=years,
            step_up_percent=step_up_percent,
            total_invested=0.0,
            future_value=0.0,
            wealth_gained=0.0,
        )

    if step_up_percent == 0.0:
        # Standard SIP: ordinary annuity * (1+r) for end-of-month deposits
        if monthly_rate == 0:
            fv = monthly_amount * n_months
        else:
            fv = monthly_amount * ((1 + monthly_rate) ** n_months - 1) / monthly_rate * (1 + monthly_rate)
        total_invested = monthly_amount * n_months
    else:
        # Step-up SIP: year-by-year accumulation
        fv = 0.0
        total_invested = 0.0
        n_full_years = int(years)
        remaining_months = n_months - n_full_years * 12

        current_monthly = monthly_amount
        for year_idx in range(n_full_years):
            months_remaining_after_year = n_months - (year_idx + 1) * 12
            # Each month in this year contributes for a certain number of months
            for month_in_year in range(12):
                months_to_grow = n_months - (year_idx * 12 + month_in_year + 1)
                if monthly_rate == 0:
                    fv += current_monthly
                else:
                    fv += current_monthly * (1 + monthly_rate) ** months_to_grow
                total_invested += current_monthly
            # Increase contribution for next year
            current_monthly *= (1 + step_up_percent / 100)

        # Handle remaining months after last full year (fractional years)
        for month_in_rem in range(remaining_months):
            months_to_grow = remaining_months - month_in_rem - 1
            if monthly_rate == 0:
                fv += current_monthly
            else:
                fv += current_monthly * (1 + monthly_rate) ** months_to_grow
            total_invested += current_monthly

        # Apply end-of-period convention: multiply by (1+r) for step-up as well
        if monthly_rate != 0:
            fv *= (1 + monthly_rate)

    wealth_gained = fv - total_invested

    return PeriodicInvestmentResult(
        monthly_amount=monthly_amount,
        annual_return=annual_return,
        years=years,
        step_up_percent=step_up_percent,
        total_invested=total_invested,
        future_value=fv,
        wealth_gained=wealth_gained,
    )
