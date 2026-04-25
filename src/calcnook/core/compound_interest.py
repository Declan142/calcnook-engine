"""Compound interest — single lump-sum growth at a constant rate.

Universal calculation. No country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompoundInterestResult:
    principal: float
    future_value: float
    interest_earned: float
    annual_rate: float
    years: float
    compounding_per_year: int

    def to_dict(self) -> dict:
        return {
            "principal": round(self.principal, 2),
            "future_value": round(self.future_value, 2),
            "interest_earned": round(self.interest_earned, 2),
            "annual_rate": self.annual_rate,
            "years": self.years,
            "compounding_per_year": self.compounding_per_year,
        }


def calculate(
    principal: float,
    annual_rate: float,
    years: float,
    compounding_per_year: int = 12,
) -> CompoundInterestResult:
    """Compute future value of a lump-sum at compound interest.

    Formula: FV = P * (1 + r/n)^(n*t)

    Args:
        principal: Initial deposit. Must be >= 0.
        annual_rate: Decimal annual rate, e.g. 0.07 for 7%.
        years: Time horizon in years. Must be >= 0.
        compounding_per_year: Times interest compounds per year.
            12 = monthly (default), 4 = quarterly, 1 = annual.

    Returns:
        CompoundInterestResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(10_000, 0.07, 10)
        >>> round(r.future_value, 2)
        20096.61
    """
    if principal < 0:
        raise ValueError("principal must be >= 0")
    if years < 0:
        raise ValueError("years must be >= 0")
    if compounding_per_year < 1:
        raise ValueError("compounding_per_year must be >= 1")

    n = compounding_per_year
    fv = principal * (1 + annual_rate / n) ** (n * years)
    interest = fv - principal

    return CompoundInterestResult(
        principal=principal,
        future_value=fv,
        interest_earned=interest,
        annual_rate=annual_rate,
        years=years,
        compounding_per_year=compounding_per_year,
    )
