"""Loan payment / EMI / mortgage amortization.

Universal calculation. No country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class LoanPaymentResult:
    principal: float
    annual_rate: float
    years: int
    monthly_payment: float
    total_payment: float
    total_interest: float
    amortization: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "principal": round(self.principal, 2),
            "annual_rate": self.annual_rate,
            "years": self.years,
            "monthly_payment": round(self.monthly_payment, 2),
            "total_payment": round(self.total_payment, 2),
            "total_interest": round(self.total_interest, 2),
        }
        if self.amortization:
            d["amortization"] = self.amortization
        return d


def calculate(
    principal: float,
    annual_rate: float,
    years: int,
    extra_monthly_payment: float = 0.0,
    include_schedule: bool = False,
) -> LoanPaymentResult:
    """Compute monthly EMI and amortization schedule for a fixed-rate loan.

    Formula (standard EMI): EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where r = monthly rate, n = total months.

    For zero-rate loans: EMI = P / n (simple equal installments).

    Args:
        principal: Loan amount. Must be > 0.
        annual_rate: Decimal annual interest rate, e.g. 0.065 for 6.5%.
            Use 0.0 for 0% / interest-free loan.
        years: Loan tenure in years. Must be >= 1.
        extra_monthly_payment: Optional additional payment above EMI each month.
            Reduces tenure effectively (schedule reflects actual payoff). Default 0.
        include_schedule: If True, computes and attaches full amortization table.
            Default False for lightweight response.

    Returns:
        LoanPaymentResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(300_000, 0.065, 30)
        >>> round(r.monthly_payment, 2)
        1896.2
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if years < 1:
        raise ValueError("years must be >= 1")
    if extra_monthly_payment < 0:
        raise ValueError("extra_monthly_payment must be >= 0")

    monthly_rate = annual_rate / 12
    n = years * 12

    if monthly_rate == 0:
        emi = principal / n
    else:
        emi = principal * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)

    schedule: List[dict] = []

    if include_schedule or extra_monthly_payment > 0:
        balance = principal
        total_paid = 0.0
        total_interest_paid = 0.0
        month = 0

        while balance > 1e-2 and month < n:
            month += 1
            interest_for_month = balance * monthly_rate
            principal_portion = min(emi - interest_for_month + extra_monthly_payment, balance)
            if principal_portion < 0:
                principal_portion = 0.0
            actual_interest = interest_for_month
            actual_payment = actual_interest + principal_portion
            balance -= principal_portion
            total_paid += actual_payment
            total_interest_paid += actual_interest

            if include_schedule:
                schedule.append({
                    "month": month,
                    "principal_paid": round(principal_portion, 2),
                    "interest_paid": round(actual_interest, 2),
                    "balance": round(max(balance, 0.0), 2),
                })

        total_payment = total_paid
        total_interest = total_interest_paid
    else:
        total_payment = emi * n
        total_interest = total_payment - principal

    return LoanPaymentResult(
        principal=principal,
        annual_rate=annual_rate,
        years=years,
        monthly_payment=round(emi, 2),
        total_payment=total_payment,
        total_interest=total_interest,
        amortization=schedule,
    )
