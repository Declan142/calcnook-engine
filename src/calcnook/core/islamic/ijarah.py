"""Ijarah — Islamic lease-to-own (Sharia auto-loan / equipment alternative).

The bank (lessor) owns the asset and leases it to the client (lessee) for a
fixed monthly rent. At the end of the lease term the ownership is transferred
to the client for a token purchase price (transfer fee). No riba; the bank's
profit is embedded in the agreed rent.

Cross-cutting module: currency-agnostic, no country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IjarahResult:
    asset_cost: float
    monthly_rent: float
    lease_years: int
    transfer_fee: float
    total_rent_paid: float
    total_cost_of_ownership: float
    effective_cost_premium: float
    effective_premium_percent: float

    def to_dict(self) -> dict:
        return {
            "asset_cost": round(self.asset_cost, 2),
            "monthly_rent": round(self.monthly_rent, 2),
            "lease_years": self.lease_years,
            "transfer_fee": round(self.transfer_fee, 2),
            "total_rent_paid": round(self.total_rent_paid, 2),
            "total_cost_of_ownership": round(self.total_cost_of_ownership, 2),
            "effective_cost_premium": round(self.effective_cost_premium, 2),
            "effective_premium_percent": round(self.effective_premium_percent, 4),
        }


def calculate(
    asset_cost: float,
    monthly_rent: float,
    lease_years: int,
    transfer_fee: float = 1.0,
) -> IjarahResult:
    """Compute Ijarah (Islamic lease-to-own) cost of ownership.

    The client pays ``monthly_rent`` for ``lease_years * 12`` months, then pays
    ``transfer_fee`` to take legal ownership of the asset. The effective premium
    shows how much more the client pays compared to outright purchase.

    Args:
        asset_cost: Market value of the asset. Must be > 0.
        monthly_rent: Agreed monthly lease payment. Must be >= 0.
        lease_years: Lease duration in years. Must be >= 1.
        transfer_fee: Token purchase price at end of lease (symbolic ownership
            transfer). Defaults to 1.0. Must be >= 0.

    Returns:
        IjarahResult with cost-of-ownership breakdown.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(30_000, 600.0, 5)
        >>> round(r.total_rent_paid, 2)
        36000.0
        >>> round(r.total_cost_of_ownership, 2)
        36001.0
    """
    if asset_cost <= 0:
        raise ValueError("asset_cost must be > 0")
    if monthly_rent < 0:
        raise ValueError("monthly_rent must be >= 0")
    if lease_years < 1:
        raise ValueError("lease_years must be >= 1")
    if transfer_fee < 0:
        raise ValueError("transfer_fee must be >= 0")

    months = lease_years * 12
    total_rent_paid = monthly_rent * months
    total_cost_of_ownership = total_rent_paid + transfer_fee
    effective_cost_premium = total_cost_of_ownership - asset_cost
    effective_premium_percent = (effective_cost_premium / asset_cost) * 100.0 if asset_cost > 0 else 0.0

    return IjarahResult(
        asset_cost=asset_cost,
        monthly_rent=monthly_rent,
        lease_years=lease_years,
        transfer_fee=transfer_fee,
        total_rent_paid=total_rent_paid,
        total_cost_of_ownership=total_cost_of_ownership,
        effective_cost_premium=effective_cost_premium,
        effective_premium_percent=effective_premium_percent,
    )
