"""India HRA (House Rent Allowance) exemption calculator — Section 10(13A).

Statutory backing:
    - Section 10(13A) of the Income-tax Act, 1961.
    - Rule 2A of the Income-tax Rules, 1962.

Exempt HRA per month is the LEAST of three numbers:
    1. Actual HRA received from the employer.
    2. Rent paid in excess of 10% of (basic + DA).
    3. 50% of (basic + DA) if the employee resides in a metro city
       (Mumbai, Delhi, Kolkata, Chennai); 40% otherwise.

The exemption is available only for the period the employee actually pays rent
and lives in rented accommodation. The remainder of HRA is taxable.

Important: HRA exemption is available ONLY under the OLD regime (Sec 115BAC
disallows it under the new regime). Caller should suppress this calc when
filing under the new regime.
"""

from __future__ import annotations

from dataclasses import dataclass


METRO_PCT = 0.50      # 50% of basic for metro cities
NON_METRO_PCT = 0.40  # 40% of basic otherwise


@dataclass(frozen=True)
class HRAExemptionResult:
    basic_monthly: float
    hra_received_monthly: float
    rent_paid_monthly: float
    is_metro: bool
    exempt_monthly: float
    exempt_annual: float
    hra_received_annual: float
    taxable_hra_annual: float
    breakdown: dict

    def to_dict(self) -> dict:
        return {
            "basic_monthly": round(self.basic_monthly, 2),
            "hra_received_monthly": round(self.hra_received_monthly, 2),
            "rent_paid_monthly": round(self.rent_paid_monthly, 2),
            "is_metro": self.is_metro,
            "exempt_monthly": round(self.exempt_monthly, 2),
            "exempt_annual": round(self.exempt_annual, 2),
            "hra_received_annual": round(self.hra_received_annual, 2),
            "taxable_hra_annual": round(self.taxable_hra_annual, 2),
            "breakdown": self.breakdown,
        }


def calculate(
    basic_monthly: float,
    hra_received_monthly: float,
    rent_paid_monthly: float,
    is_metro: bool,
) -> HRAExemptionResult:
    """Compute HRA exemption under Section 10(13A) / Rule 2A.

    Exempt = min(actual_hra, rent - 0.10 × basic, basic_pct × basic), floored at 0.

    Args:
        basic_monthly: Monthly basic salary (incl. DA forming part of retirement
            benefits) in INR.
        hra_received_monthly: Monthly HRA received from employer in INR.
        rent_paid_monthly: Actual monthly rent paid by employee in INR.
        is_metro: True if employee resides in Mumbai / Delhi / Kolkata / Chennai
            (the four classical metros under Sec 10(13A)). False otherwise.

    Returns:
        HRAExemptionResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(
        ...     basic_monthly=50_000,
        ...     hra_received_monthly=20_000,
        ...     rent_paid_monthly=18_000,
        ...     is_metro=True,
        ... )
        >>> r.exempt_monthly
        13000.0
    """
    if basic_monthly < 0:
        raise ValueError("basic_monthly must be >= 0")
    if hra_received_monthly < 0:
        raise ValueError("hra_received_monthly must be >= 0")
    if rent_paid_monthly < 0:
        raise ValueError("rent_paid_monthly must be >= 0")

    actual_hra = hra_received_monthly
    rent_minus_10pct = rent_paid_monthly - 0.10 * basic_monthly
    basic_pct = (METRO_PCT if is_metro else NON_METRO_PCT) * basic_monthly

    candidates = [actual_hra, rent_minus_10pct, basic_pct]
    applied_min_value = min(candidates)
    exempt_monthly = max(0.0, applied_min_value)

    # Identify which limb bound the result (for the breakdown).
    if abs(applied_min_value - actual_hra) < 1e-9:
        applied_min_label = "actual_hra"
    elif abs(applied_min_value - rent_minus_10pct) < 1e-9:
        applied_min_label = "rent_minus_10pct_basic"
    else:
        applied_min_label = "basic_pct"

    exempt_annual = exempt_monthly * 12.0
    hra_received_annual = hra_received_monthly * 12.0
    taxable_hra_annual = max(0.0, hra_received_annual - exempt_annual)

    breakdown = {
        "actual_hra_monthly": round(actual_hra, 2),
        "rent_minus_10pct_basic_monthly": round(rent_minus_10pct, 2),
        "basic_pct_monthly": round(basic_pct, 2),
        "metro_pct_used": METRO_PCT if is_metro else NON_METRO_PCT,
        "applied_min": applied_min_label,
        "regime_note": "HRA exemption available only under OLD regime (Sec 115BAC disallows under new regime).",
    }

    return HRAExemptionResult(
        basic_monthly=basic_monthly,
        hra_received_monthly=hra_received_monthly,
        rent_paid_monthly=rent_paid_monthly,
        is_metro=is_metro,
        exempt_monthly=exempt_monthly,
        exempt_annual=exempt_annual,
        hra_received_annual=hra_received_annual,
        taxable_hra_annual=taxable_hra_annual,
        breakdown=breakdown,
    )
