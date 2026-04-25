"""Australia income tax + Medicare Levy + HECS-HELP repayment for 2025/26.

Reported as 2026 assessment year per project convention.

HECS simplification: the full ATO sliding-scale compulsory repayment schedule
has ~18 thresholds. We implement the main bands used in practice. This is
documented as a simplification — callers should verify with ato.gov.au for
official figures.

Reference: ATO 2025-26 tax rates and HECS compulsory repayment thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# 2025/26 AU income tax brackets (lower_inclusive, upper_inclusive, base_tax, rate)
# Applied on whole income, not income above a threshold.
# ---------------------------------------------------------------------------
# Bracket structure: (lower_bound, upper_bound, fixed_tax_at_lower, marginal_rate)
_BRACKETS = [
    (0, 18_200, 0, 0.0),
    (18_201, 45_000, 0, 0.16),
    (45_001, 135_000, 4_288, 0.30),
    (135_001, 190_000, 31_288, 0.37),
    (190_001, float("inf"), 51_638, 0.45),
]

# Medicare Levy
MEDICARE_RATE = 0.02
MEDICARE_PHASE_IN_LOWER = 26_000.0  # below this: no Medicare
MEDICARE_PHASE_IN_UPPER = 32_500.0  # fully phased in above this (approx)

# HECS-HELP repayment thresholds 2025/26 (simplified progressive bands)
# Format: (upper_threshold, repayment_rate)
_HECS_BANDS = [
    (54_434, 0.000),
    (62_850, 0.010),
    (66_620, 0.020),
    (70_618, 0.025),
    (74_855, 0.030),
    (79_347, 0.035),
    (84_108, 0.040),
    (88_756, 0.045),
    (93_669, 0.050),
    (99_069, 0.055),
    (104_872, 0.060),
    (111_142, 0.065),
    (117_894, 0.070),
    (124_950, 0.075),
    (132_469, 0.080),
    (140_417, 0.085),
    (148_845, 0.090),
    (157_775, 0.095),
    (float("inf"), 0.100),
]


@dataclass(frozen=True)
class AUBracketDetail:
    """Single income-tax bracket contribution."""
    rate: float
    income_in_bracket: float
    tax_in_bracket: float

    def to_dict(self) -> dict:
        return {
            "rate": self.rate,
            "income_in_bracket": round(self.income_in_bracket, 2),
            "tax_in_bracket": round(self.tax_in_bracket, 2),
        }


@dataclass(frozen=True)
class AUIncomeTaxResult:
    """Result of an Australian income tax calculation."""
    gross_income: float
    year: int
    has_hecs_debt: bool
    income_tax: float
    medicare_levy: float
    hecs_repayment: float
    total_tax: float
    effective_rate: float
    take_home: float
    bracket_breakdown: tuple

    def to_dict(self) -> dict:
        return {
            "gross_income": round(self.gross_income, 2),
            "year": self.year,
            "has_hecs_debt": self.has_hecs_debt,
            "income_tax": round(self.income_tax, 2),
            "medicare_levy": round(self.medicare_levy, 2),
            "hecs_repayment": round(self.hecs_repayment, 2),
            "total_tax": round(self.total_tax, 2),
            "effective_rate": round(self.effective_rate, 6),
            "take_home": round(self.take_home, 2),
            "bracket_breakdown": [b.to_dict() for b in self.bracket_breakdown],
        }


def calculate(
    income: float,
    has_hecs_debt: bool = False,
    year: int = 2026,
) -> AUIncomeTaxResult:
    """Compute Australian income tax, Medicare Levy, and optional HECS-HELP repayment.

    Uses the Stage 3 tax cuts brackets effective from 1 July 2024 (2024-25 and
    2025-26 financial years). The calculation does NOT include Low Income Tax
    Offset (LITO), Low and Middle Income Tax Offset (LMITO — abolished), or
    other offsets. Call ATO tax calculator for the full offset picture.

    HECS-HELP note: compulsory repayment is based on your Repayment Income
    (broadly, taxable income + reportable fringe benefits + total net investment
    losses). We use gross income as an approximation. The 18-step ATO sliding
    scale is implemented in simplified form — see module constants for thresholds.

    Medicare Levy: 2% of income with a phase-in between $26,000–$32,500 for low
    earners (full levy applies from ~$32,500).

    Args:
        income: Gross annual income in AUD.
        has_hecs_debt: Whether HECS-HELP compulsory repayment applies.
        year: Only 2026 (FY 2025/26) is supported.

    Returns:
        AUIncomeTaxResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(80_000)
        >>> round(r.income_tax, 2)
        14_288.0
    """
    if income < 0:
        raise ValueError("income must be >= 0")
    if year != 2026:
        raise ValueError("Only year=2026 (FY 2025/26) is available in this version")

    # Income tax via brackets
    breakdown: List[AUBracketDetail] = []
    it = 0.0
    for lower, upper, base, rate in _BRACKETS:
        if income < lower:
            break
        chunk = min(income, upper if upper != float("inf") else income) - (lower - 1)
        chunk = max(0.0, chunk)
        if rate == 0.0:
            breakdown.append(AUBracketDetail(rate=0.0, income_in_bracket=chunk, tax_in_bracket=0.0))
            continue
        # Re-derive from base + marginal for clarity
        chunk_tax = chunk * rate
        it += chunk_tax
        breakdown.append(AUBracketDetail(rate=rate, income_in_bracket=chunk, tax_in_bracket=chunk_tax))

    # Medicare Levy with phase-in
    if income <= MEDICARE_PHASE_IN_LOWER:
        ml = 0.0
    elif income <= MEDICARE_PHASE_IN_UPPER:
        # Phase-in: 10% of (income - lower_threshold) until full levy kicks in
        ml = (income - MEDICARE_PHASE_IN_LOWER) * 0.10
    else:
        ml = income * MEDICARE_RATE

    # HECS-HELP compulsory repayment
    hecs = 0.0
    if has_hecs_debt:
        for upper, rate in _HECS_BANDS:
            if income <= upper:
                hecs = income * rate
                break

    total_tax = it + ml + hecs
    effective_rate = total_tax / income if income > 0 else 0.0
    take_home = income - total_tax

    return AUIncomeTaxResult(
        gross_income=income,
        year=year,
        has_hecs_debt=has_hecs_debt,
        income_tax=it,
        medicare_levy=ml,
        hecs_repayment=hecs,
        total_tax=total_tax,
        effective_rate=effective_rate,
        take_home=take_home,
        bracket_breakdown=tuple(breakdown),
    )
