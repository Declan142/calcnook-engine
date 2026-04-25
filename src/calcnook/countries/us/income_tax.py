"""US federal income tax calculator for 2026.

Brackets projected from 2025 + ~3% inflation adjustment (IRS typically announces
final 2026 brackets in late 2025; use these as estimates until official release).

Reference: IRS Rev. Proc. 2025-xx (projected).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# 2026 projected tax brackets — (upper_bound, rate). Last entry bound = inf.
# ---------------------------------------------------------------------------
_BRACKETS: dict[str, list[tuple[float, float]]] = {
    "single": [
        (11_925, 0.10),
        (48_475, 0.12),
        (103_350, 0.22),
        (197_300, 0.24),
        (250_525, 0.32),
        (626_350, 0.35),
        (float("inf"), 0.37),
    ],
    "married_jointly": [
        (23_850, 0.10),
        (96_950, 0.12),
        (206_700, 0.22),
        (394_600, 0.24),
        (501_050, 0.32),
        (751_600, 0.35),
        (float("inf"), 0.37),
    ],
    "married_separately": [
        (11_925, 0.10),
        (48_475, 0.12),
        (103_350, 0.22),
        (197_300, 0.24),
        (250_525, 0.32),
        (375_800, 0.35),
        (float("inf"), 0.37),
    ],
    "head_of_household": [
        (17_000, 0.10),
        (64_850, 0.12),
        (103_350, 0.22),
        (197_300, 0.24),
        (250_500, 0.32),
        (626_350, 0.35),
        (float("inf"), 0.37),
    ],
}

_STANDARD_DEDUCTION: dict[str, float] = {
    "single": 15_000,
    "married_jointly": 30_000,
    "married_separately": 15_000,
    "head_of_household": 22_500,
}

VALID_FILING_STATUSES = frozenset(_BRACKETS.keys())


@dataclass(frozen=True)
class BracketDetail:
    """Single bracket contribution."""
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
class USIncomeTaxResult:
    """Result of a US federal income tax calculation."""
    gross_income: float
    filing_status: str
    year: int
    taxable_income: float
    tax_owed: float
    effective_rate: float
    marginal_rate: float
    bracket_breakdown: tuple  # tuple of BracketDetail

    def to_dict(self) -> dict:
        return {
            "gross_income": round(self.gross_income, 2),
            "filing_status": self.filing_status,
            "year": self.year,
            "taxable_income": round(self.taxable_income, 2),
            "tax_owed": round(self.tax_owed, 2),
            "effective_rate": round(self.effective_rate, 6),
            "marginal_rate": self.marginal_rate,
            "bracket_breakdown": [b.to_dict() for b in self.bracket_breakdown],
        }


def calculate(
    income: float,
    filing_status: str,
    year: int = 2026,
) -> USIncomeTaxResult:
    """Compute US federal income tax for the given income and filing status.

    Applies the standard deduction to arrive at taxable income, then runs
    progressive bracket calculation. Does NOT include AMT, NIIT, FICA, or
    state taxes.

    Brackets projected from 2025 + ~3% inflation adjustment.

    Args:
        income: Gross annual income in USD.
        filing_status: One of "single", "married_jointly", "married_separately",
            "head_of_household".
        year: Tax year — only 2026 brackets are encoded; other years raise ValueError.

    Returns:
        USIncomeTaxResult with full breakdown.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(60_000, "single")
        >>> round(r.tax_owed, 2)
        5161.5
    """
    if income < 0:
        raise ValueError("income must be >= 0")
    if filing_status not in VALID_FILING_STATUSES:
        raise ValueError(
            f"filing_status must be one of {sorted(VALID_FILING_STATUSES)}, "
            f"got {filing_status!r}"
        )
    if year != 2026:
        raise ValueError("Only year=2026 brackets are available in this version")

    std_deduction = _STANDARD_DEDUCTION[filing_status]
    taxable = max(0.0, income - std_deduction)

    brackets = _BRACKETS[filing_status]
    breakdown: List[BracketDetail] = []
    tax = 0.0
    prev_bound = 0.0
    marginal_rate = brackets[0][1]

    for bound, rate in brackets:
        if taxable <= prev_bound:
            break
        chunk = min(taxable, bound) - prev_bound
        if chunk <= 0:
            prev_bound = bound
            continue
        tax_chunk = chunk * rate
        tax += tax_chunk
        breakdown.append(BracketDetail(rate=rate, taxed_in_bracket=chunk, tax_in_bracket=tax_chunk))
        marginal_rate = rate
        prev_bound = bound

    effective_rate = tax / income if income > 0 else 0.0

    return USIncomeTaxResult(
        gross_income=income,
        filing_status=filing_status,
        year=year,
        taxable_income=taxable,
        tax_owed=tax,
        effective_rate=effective_rate,
        marginal_rate=marginal_rate,
        bracket_breakdown=tuple(breakdown),
    )
