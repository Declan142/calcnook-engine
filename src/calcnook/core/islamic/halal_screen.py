"""Halal Stock Screener — AAOIFI Sharia compliance check for equities.

Applies the AAOIFI (Accounting and Auditing Organisation for Islamic Financial
Institutions) standard financial ratio screens and business-activity exclusions
to determine whether a stock is Sharia-compliant.

A stock FAILS if ANY of the following conditions hold:
  1. Business activity falls in a prohibited (haram) sector.
  2. Interest-bearing debt / market cap > 33%.
  3. Cash + interest-bearing securities / market cap > 33%.
  4. Receivables / market cap > 49% (liquidity / debt-trading concern).
  5. Haram revenue / total revenue > 5% (purification threshold).

Cross-cutting module: no country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HARAM_SECTORS: tuple[str, ...] = (
    "alcohol",
    "gambling",
    "conventional financial",
    "banking",
    "conventional banking",
    "pork",
    "weapons of mass destruction",
    "adult entertainment",
    "pornography",
    "tobacco",
)

# Ratio thresholds (AAOIFI standard)
_DEBT_THRESHOLD = 0.33
_CASH_THRESHOLD = 0.33
_RECEIVABLES_THRESHOLD = 0.49
_HARAM_REVENUE_THRESHOLD = 0.05


@dataclass(frozen=True)
class ScreenResult:
    is_compliant: bool
    failed_checks: list[str]
    ratios: dict[str, float]
    purification_ratio: float  # haram_revenue / total_revenue; caller multiplies by holding %

    def to_dict(self) -> dict:
        return {
            "is_compliant": self.is_compliant,
            "failed_checks": list(self.failed_checks),
            "ratios": {k: round(v, 6) for k, v in self.ratios.items()},
            "purification_ratio": round(self.purification_ratio, 6),
        }


def screen(
    sector: str,
    market_cap: float,
    debt_interest_bearing: float,
    cash_and_interest_securities: float,
    receivables: float,
    total_revenue: float,
    haram_revenue: float,
) -> ScreenResult:
    """Screen a stock for Sharia compliance per AAOIFI standard ratios.

    Args:
        sector: Business sector / activity description. Case-insensitive.
            Compared against ``HARAM_SECTORS``.
        market_cap: Total market capitalisation. Must be > 0.
        debt_interest_bearing: Total interest-bearing debt on the balance sheet.
            Must be >= 0.
        cash_and_interest_securities: Cash plus any interest-bearing securities
            (e.g. conventional bonds) held by the company. Must be >= 0.
        receivables: Total accounts receivable. Must be >= 0.
        total_revenue: Total annual revenue. Must be > 0.
        haram_revenue: Portion of revenue from non-compliant activities.
            Must be >= 0 and <= total_revenue.

    Returns:
        ScreenResult with compliance verdict, failed check list, computed
        ratios, and purification ratio.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = screen("technology", 1_000_000, 100_000, 50_000, 200_000, 500_000, 10_000)
        >>> r.is_compliant
        True
    """
    if market_cap <= 0:
        raise ValueError("market_cap must be > 0")
    if debt_interest_bearing < 0:
        raise ValueError("debt_interest_bearing must be >= 0")
    if cash_and_interest_securities < 0:
        raise ValueError("cash_and_interest_securities must be >= 0")
    if receivables < 0:
        raise ValueError("receivables must be >= 0")
    if total_revenue <= 0:
        raise ValueError("total_revenue must be > 0")
    if haram_revenue < 0:
        raise ValueError("haram_revenue must be >= 0")
    if haram_revenue > total_revenue:
        raise ValueError("haram_revenue cannot exceed total_revenue")

    failed_checks: list[str] = []

    # 1. Business activity screen
    sector_lower = sector.strip().lower()
    sector_is_haram = any(h in sector_lower for h in HARAM_SECTORS)
    if sector_is_haram:
        failed_checks.append(f"haram_sector: '{sector}' is in a prohibited business activity")

    # 2. Debt ratio
    debt_ratio = debt_interest_bearing / market_cap
    if debt_ratio > _DEBT_THRESHOLD:
        failed_checks.append(
            f"debt_ratio: {debt_ratio:.4f} > {_DEBT_THRESHOLD} threshold"
        )

    # 3. Cash + interest-bearing securities ratio
    cash_ratio = cash_and_interest_securities / market_cap
    if cash_ratio > _CASH_THRESHOLD:
        failed_checks.append(
            f"cash_ratio: {cash_ratio:.4f} > {_CASH_THRESHOLD} threshold"
        )

    # 4. Receivables ratio
    receivables_ratio = receivables / market_cap
    if receivables_ratio > _RECEIVABLES_THRESHOLD:
        failed_checks.append(
            f"receivables_ratio: {receivables_ratio:.4f} > {_RECEIVABLES_THRESHOLD} threshold"
        )

    # 5. Haram revenue ratio
    haram_revenue_ratio = haram_revenue / total_revenue
    if haram_revenue_ratio > _HARAM_REVENUE_THRESHOLD:
        failed_checks.append(
            f"haram_revenue_ratio: {haram_revenue_ratio:.4f} > {_HARAM_REVENUE_THRESHOLD} threshold"
        )

    ratios = {
        "debt_ratio": debt_ratio,
        "cash_ratio": cash_ratio,
        "receivables_ratio": receivables_ratio,
        "haram_revenue_ratio": haram_revenue_ratio,
    }

    return ScreenResult(
        is_compliant=len(failed_checks) == 0,
        failed_checks=failed_checks,
        ratios=ratios,
        purification_ratio=haram_revenue_ratio,
    )
