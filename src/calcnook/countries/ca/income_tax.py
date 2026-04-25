"""Canada federal income tax calculator for 2026.

Brackets projected from 2025 + ~3% inflation adjustment.
Provincial tax is accepted as a parameter stub and returns 0 pending full
implementation (documented as TODO).

Reference: CRA T4012 (projected 2026). Basic Personal Amount credit at 15%.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# 2026 projected federal brackets (upper_bound, rate). Last entry bound = inf.
# ---------------------------------------------------------------------------
_FEDERAL_BRACKETS = [
    (57_376, 0.15),
    (114_750, 0.205),
    (177_882, 0.26),
    (253_414, 0.29),
    (float("inf"), 0.33),
]

# Basic Personal Amount — generates a 15% non-refundable tax credit
BASIC_PERSONAL_AMOUNT = 16_500.0
BASIC_PERSONAL_CREDIT_RATE = 0.15


@dataclass(frozen=True)
class CABracketDetail:
    """Single federal bracket contribution."""
    rate: float
    taxed_in_bracket: float
    tax_in_bracket: float

    def to_dict(self) -> dict:
        return {
            "rate": self.rate,
            "taxed_in_bracket": round(self.taxed_in_bracket, 2),
            "tax_in_bracket": round(self.tax_in_bracket, 2),
        }


@dataclass(frozen=True)
class CAIncomeTaxResult:
    """Result of a Canada federal income tax calculation."""
    gross_income: float
    province: Optional[str]
    year: int
    taxable_income: float
    federal_tax_before_credits: float
    basic_personal_credit: float
    tax_owed: float             # federal tax after credits (provincial = 0 — TODO)
    provincial_tax: float       # always 0.0 (TODO: implement province-by-province)
    effective_rate: float
    marginal_rate: float
    bracket_breakdown: tuple

    def to_dict(self) -> dict:
        return {
            "gross_income": round(self.gross_income, 2),
            "province": self.province,
            "year": self.year,
            "taxable_income": round(self.taxable_income, 2),
            "federal_tax_before_credits": round(self.federal_tax_before_credits, 2),
            "basic_personal_credit": round(self.basic_personal_credit, 2),
            "tax_owed": round(self.tax_owed, 2),
            "provincial_tax": round(self.provincial_tax, 2),
            "effective_rate": round(self.effective_rate, 6),
            "marginal_rate": self.marginal_rate,
            "bracket_breakdown": [b.to_dict() for b in self.bracket_breakdown],
        }


def calculate(
    income: float,
    province: Optional[str] = None,
    year: int = 2026,
) -> CAIncomeTaxResult:
    """Compute Canada federal income tax for 2026.

    Provincial tax is NOT computed — `provincial_tax` is always 0.0. This is
    a known limitation (TODO). For an accurate marginal rate, add provincial
    tax on top of the federal result.

    Federal tax uses progressive brackets on gross income (Canada does not have
    a flat standard deduction; the Basic Personal Amount is a non-refundable
    credit at 15% rate applied against computed federal tax).

    Brackets projected from 2025 + ~3% inflation adjustment.

    Args:
        income: Gross annual income in CAD.
        province: Two-letter province/territory code (e.g. "ON", "BC"). Accepted
            but ignored — provincial computation is a TODO stub.
        year: Only 2026 is supported.

    Returns:
        CAIncomeTaxResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(100_000)
        >>> round(r.tax_owed, 2)
        14869.32
    """
    if income < 0:
        raise ValueError("income must be >= 0")
    if year != 2026:
        raise ValueError("Only year=2026 brackets are available in this version")

    taxable = income  # Canada uses total income on the federal return directly

    breakdown: List[CABracketDetail] = []
    tax_gross = 0.0
    prev = 0.0
    marginal_rate = _FEDERAL_BRACKETS[0][1]

    for bound, rate in _FEDERAL_BRACKETS:
        if taxable <= prev:
            break
        chunk = min(taxable, bound) - prev
        if chunk <= 0:
            prev = bound
            continue
        t = chunk * rate
        tax_gross += t
        breakdown.append(CABracketDetail(rate=rate, taxed_in_bracket=chunk, tax_in_bracket=t))
        marginal_rate = rate
        prev = bound

    # Basic Personal Amount non-refundable credit
    bpa_credit = BASIC_PERSONAL_AMOUNT * BASIC_PERSONAL_CREDIT_RATE
    tax_net = max(0.0, tax_gross - bpa_credit)

    effective_rate = tax_net / income if income > 0 else 0.0

    return CAIncomeTaxResult(
        gross_income=income,
        province=province,
        year=year,
        taxable_income=taxable,
        federal_tax_before_credits=tax_gross,
        basic_personal_credit=bpa_credit,
        tax_owed=tax_net,
        provincial_tax=0.0,
        effective_rate=effective_rate,
        marginal_rate=marginal_rate,
        bracket_breakdown=tuple(breakdown),
    )
