"""Murabaha — cost-plus financing (Sharia mortgage / asset-purchase alternative).

The bank buys an asset and resells it to the client at an agreed markup,
payable in fixed installments. No riba (interest) is charged; the profit is
embedded in the sale price at the outset.

Cross-cutting module: currency-agnostic, no country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MurabahaResult:
    asset_cost: float
    markup_percent: float
    tenure_years: int
    down_payment: float
    total_sale_price: float
    principal_financed: float
    monthly_installment: float
    total_paid: float
    total_markup: float
    effective_apr_equivalent: float  # IRR-based, for transparency comparison

    def to_dict(self) -> dict:
        return {
            "asset_cost": round(self.asset_cost, 2),
            "markup_percent": self.markup_percent,
            "tenure_years": self.tenure_years,
            "down_payment": round(self.down_payment, 2),
            "total_sale_price": round(self.total_sale_price, 2),
            "principal_financed": round(self.principal_financed, 2),
            "monthly_installment": round(self.monthly_installment, 2),
            "total_paid": round(self.total_paid, 2),
            "total_markup": round(self.total_markup, 2),
            "effective_apr_equivalent": round(self.effective_apr_equivalent, 6),
        }


def _conventional_apr_equivalent(
    principal: float,
    monthly_payment: float,
    months: int,
    iterations: int = 60,
) -> float:
    """Find the annualised rate (APR) of a conventional loan with identical terms.

    Solves for the monthly rate ``r`` such that the present value of
    ``monthly_payment`` for ``months`` equals ``principal``:

        principal = monthly_payment * (1 - (1+r)^-n) / r

    Uses bisection over monthly rate ∈ (0, 1]. Returns APR = (1+r)^12 - 1.

    When monthly_payment * months == principal (zero cost financing, zero APR),
    returns 0.0.

    Args:
        principal: Loan amount (asset_cost or principal_financed).
        monthly_payment: Fixed monthly payment.
        months: Number of payment periods.
        iterations: Bisection steps.

    Returns:
        Annualised equivalent rate as decimal (e.g. 0.114 for 11.4%).
    """
    total_repaid = monthly_payment * months
    if total_repaid <= principal:
        return 0.0

    def pv_annuity(r: float) -> float:
        if r <= 0:
            return monthly_payment * months
        return monthly_payment * (1 - (1 + r) ** (-months)) / r

    lo, hi = 1e-9, 1.0  # monthly rate bounds
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if pv_annuity(mid) > principal:
            lo = mid
        else:
            hi = mid

    monthly_rate = (lo + hi) / 2.0
    return (1 + monthly_rate) ** 12 - 1


def calculate(
    asset_cost: float,
    markup_percent: float,
    tenure_years: int,
    down_payment: float = 0.0,
) -> MurabahaResult:
    """Compute Murabaha financing details for an asset purchase.

    The bank acquires the asset at `asset_cost` and immediately resells it to
    the client at ``total_sale_price = asset_cost * (1 + markup_percent / 100)``.
    The client pays `down_payment` upfront and the balance in equal monthly
    installments over ``tenure_years * 12`` months.

    The effective APR equivalent is the annualised IRR of the client's cashflow
    stream (down_payment at t=0, monthly installments thereafter), computed by
    bisection — intended as a transparency comparison with a conventional loan,
    NOT as an interest charge.

    Args:
        asset_cost: Purchase price the bank pays for the asset. Must be > 0.
        markup_percent: Total agreed markup expressed as a percentage of
            ``asset_cost`` (e.g. 30.0 for 30% over the whole tenure). Must be >= 0.
        tenure_years: Number of years over which installments are paid. Must be >= 1.
        down_payment: Upfront payment by the client. Must be >= 0 and
            < total_sale_price.

    Returns:
        MurabahaResult with all financing details.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(100_000, 30.0, 5)
        >>> round(r.total_sale_price, 2)
        130000.0
        >>> round(r.monthly_installment, 2)
        2166.67
    """
    if asset_cost <= 0:
        raise ValueError("asset_cost must be > 0")
    if markup_percent < 0:
        raise ValueError("markup_percent must be >= 0")
    if tenure_years < 1:
        raise ValueError("tenure_years must be >= 1")
    if down_payment < 0:
        raise ValueError("down_payment must be >= 0")

    total_sale_price = asset_cost * (1 + markup_percent / 100.0)
    total_markup = total_sale_price - asset_cost

    if down_payment >= total_sale_price:
        raise ValueError("down_payment must be less than total_sale_price")

    principal_financed = total_sale_price - down_payment
    months = tenure_years * 12
    monthly_installment = principal_financed / months
    total_paid = down_payment + monthly_installment * months

    # Effective APR equivalent: the conventional loan rate that would produce
    # the same monthly payment for the same asset cost (principal). This is a
    # transparency disclosure, not an interest charge. We compare against
    # asset_cost (what a conventional lender would advance) not total_sale_price.
    effective_apr_equivalent = _conventional_apr_equivalent(
        principal=asset_cost - down_payment,
        monthly_payment=monthly_installment,
        months=months,
    )

    return MurabahaResult(
        asset_cost=asset_cost,
        markup_percent=markup_percent,
        tenure_years=tenure_years,
        down_payment=down_payment,
        total_sale_price=total_sale_price,
        principal_financed=principal_financed,
        monthly_installment=monthly_installment,
        total_paid=total_paid,
        total_markup=total_markup,
        effective_apr_equivalent=effective_apr_equivalent,
    )
