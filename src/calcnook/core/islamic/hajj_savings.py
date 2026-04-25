"""Hajj Savings Planner — target-based monthly savings to fund pilgrimage.

Computes the monthly contribution needed to accumulate a Hajj cost target
within a given number of years, accounting for current savings invested in
a halal (e.g. sukuk / equity) instrument at an expected annual return.

Cross-cutting module: currency-agnostic, no country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HajjSavingsResult:
    hajj_cost_target: float
    years_to_hajj: int
    current_savings: float
    expected_annual_return: float
    monthly_contribution_needed: float
    total_contribution: float
    expected_growth: float  # interest/return earned on contributions + savings
    target_met_at_zero_contribution: bool  # current savings already enough

    def to_dict(self) -> dict:
        return {
            "hajj_cost_target": round(self.hajj_cost_target, 2),
            "years_to_hajj": self.years_to_hajj,
            "current_savings": round(self.current_savings, 2),
            "expected_annual_return": self.expected_annual_return,
            "monthly_contribution_needed": round(self.monthly_contribution_needed, 2),
            "total_contribution": round(self.total_contribution, 2),
            "expected_growth": round(self.expected_growth, 2),
            "target_met_at_zero_contribution": self.target_met_at_zero_contribution,
        }


def calculate(
    hajj_cost_target: float,
    years_to_hajj: int,
    current_savings: float = 0.0,
    expected_annual_return: float = 0.0,
) -> HajjSavingsResult:
    """Compute monthly savings needed to reach a Hajj cost target.

    Uses the future-value-of-annuity-due formula (contributions at start of
    each month):

        FV_savings = current_savings * (1+r)^n
        FV_annuity = monthly * (((1+r)^n - 1) / r) * (1+r)   [if r > 0]
        FV_annuity = monthly * n                               [if r == 0]

    Solves for ``monthly`` such that FV_savings + FV_annuity >= target.

    If current savings already exceed the target's future requirement,
    ``monthly_contribution_needed`` is 0 and ``target_met_at_zero_contribution``
    is True.

    Args:
        hajj_cost_target: Total cost of Hajj in today's currency. Must be > 0.
        years_to_hajj: Years until Hajj trip. Must be >= 1.
        current_savings: Existing savings already invested. Must be >= 0.
        expected_annual_return: Expected annual halal investment return as a
            decimal (e.g. 0.06 for 6%). Must be >= 0.

    Returns:
        HajjSavingsResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(10_000, 5, current_savings=0, expected_annual_return=0.06)
        >>> round(r.monthly_contribution_needed, 2)
        143.33
    """
    if hajj_cost_target <= 0:
        raise ValueError("hajj_cost_target must be > 0")
    if years_to_hajj < 1:
        raise ValueError("years_to_hajj must be >= 1")
    if current_savings < 0:
        raise ValueError("current_savings must be >= 0")
    if expected_annual_return < 0:
        raise ValueError("expected_annual_return must be >= 0")

    n = years_to_hajj * 12  # total months
    r = expected_annual_return / 12.0  # monthly rate

    # Future value of existing savings
    fv_savings = current_savings * ((1 + r) ** n)

    # Remaining target after savings grow
    remaining = hajj_cost_target - fv_savings

    if remaining <= 0:
        # Already met — no contributions needed
        return HajjSavingsResult(
            hajj_cost_target=hajj_cost_target,
            years_to_hajj=years_to_hajj,
            current_savings=current_savings,
            expected_annual_return=expected_annual_return,
            monthly_contribution_needed=0.0,
            total_contribution=0.0,
            expected_growth=round(fv_savings - current_savings, 10),
            target_met_at_zero_contribution=True,
        )

    # Solve for monthly contribution using annuity-due FV formula
    if r == 0:
        monthly = remaining / n
    else:
        # annuity_due factor = (((1+r)^n - 1) / r) * (1+r)
        annuity_factor = (((1 + r) ** n - 1) / r) * (1 + r)
        monthly = remaining / annuity_factor

    total_contribution = monthly * n
    # Total actually accumulated = fv_savings + (contributions * annuity factor)
    if r == 0:
        fv_annuity = monthly * n
    else:
        fv_annuity = monthly * (((1 + r) ** n - 1) / r) * (1 + r)

    total_accumulated = fv_savings + fv_annuity
    expected_growth = total_accumulated - current_savings - total_contribution

    return HajjSavingsResult(
        hajj_cost_target=hajj_cost_target,
        years_to_hajj=years_to_hajj,
        current_savings=current_savings,
        expected_annual_return=expected_annual_return,
        monthly_contribution_needed=monthly,
        total_contribution=total_contribution,
        expected_growth=expected_growth,
        target_met_at_zero_contribution=False,
    )
