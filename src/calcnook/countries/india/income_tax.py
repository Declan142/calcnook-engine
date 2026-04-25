"""India income tax calculator — New Regime FY 2025-26 (AY 2026-27).

New Regime is the default from FY 2023-24 onwards per Finance Act 2023.
Old regime is retained as a stub with a note that it is not optimized here.

New Regime brackets FY 2025-26 (Finance Act 2025 / Union Budget 2025):
    Nil      : up to ₹4,00,000
    5%       : ₹4,00,001 – ₹8,00,000
    10%      : ₹8,00,001 – ₹12,00,000
    15%      : ₹12,00,001 – ₹16,00,000
    20%      : ₹16,00,001 – ₹20,00,000
    25%      : ₹20,00,001 – ₹24,00,000
    30%      : above ₹24,00,000

Standard deduction (new regime): ₹75,000 (applicable for salaried individuals).
Section 87A rebate: full tax rebate if taxable income ≤ ₹12,00,000 (max ₹60,000).
Health & Education Cess: 4% on tax after rebate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# New regime brackets (upper_bound, rate). Last bound = inf.
# ---------------------------------------------------------------------------
_NEW_REGIME_BRACKETS = [
    (400_000, 0.00),
    (800_000, 0.05),
    (1_200_000, 0.10),
    (1_600_000, 0.15),
    (2_000_000, 0.20),
    (2_400_000, 0.25),
    (float("inf"), 0.30),
]

STANDARD_DEDUCTION_NEW = 75_000.0
REBATE_87A_MAX = 60_000.0
REBATE_87A_INCOME_LIMIT = 1_200_000.0
CESS_RATE = 0.04

VALID_REGIMES = frozenset({"new", "old"})


@dataclass(frozen=True)
class INBracketDetail:
    """Single tax bracket contribution."""
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
class INIncomeTaxResult:
    """Result of an Indian income tax calculation."""
    gross_income: float
    regime: str
    year: int
    standard_deduction: float
    taxable_income: float
    tax_before_rebate: float
    rebate_87a: float
    tax_after_rebate: float
    health_education_cess: float
    tax_owed: float
    effective_rate: float
    marginal_rate: float
    bracket_breakdown: tuple

    def to_dict(self) -> dict:
        return {
            "gross_income": round(self.gross_income, 2),
            "regime": self.regime,
            "year": self.year,
            "standard_deduction": round(self.standard_deduction, 2),
            "taxable_income": round(self.taxable_income, 2),
            "tax_before_rebate": round(self.tax_before_rebate, 2),
            "rebate_87a": round(self.rebate_87a, 2),
            "tax_after_rebate": round(self.tax_after_rebate, 2),
            "health_education_cess": round(self.health_education_cess, 2),
            "tax_owed": round(self.tax_owed, 2),
            "effective_rate": round(self.effective_rate, 6),
            "marginal_rate": self.marginal_rate,
            "bracket_breakdown": [b.to_dict() for b in self.bracket_breakdown],
        }


def calculate(
    gross_income: float,
    regime: str = "new",
    year: int = 2026,
) -> INIncomeTaxResult:
    """Compute Indian income tax for FY 2025-26 (AY 2026-27).

    New regime is the default per Finance Act 2023. The old regime is accepted
    but returns a stub result with a warning — old-regime deductions (80C, 80D,
    HRA, etc.) vary per individual and are not fully modelled here.

    Section 87A rebate applies when taxable income ≤ ₹12,00,000 (new regime).
    The rebate is the lesser of computed tax and ₹60,000 — effectively making
    net income up to ₹12L tax-free in the new regime.

    Health & Education Cess: 4% on tax payable after rebate.

    Standard deduction ₹75,000 applies for salaried individuals. Non-salaried
    income (business, profession) may have different deductions — pass taxable
    income directly if deductions are pre-computed.

    Args:
        gross_income: Gross annual income in INR (total income from all sources
            before the standard deduction for salaried individuals).
        regime: "new" (default) or "old" (stub — not fully modelled).
        year: Only 2026 (AY 2026-27) is fully supported.

    Returns:
        INIncomeTaxResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(1_000_000)
        >>> r.tax_owed  # effective 0 due to 87A rebate
        0.0
    """
    if gross_income < 0:
        raise ValueError("gross_income must be >= 0")
    if regime not in VALID_REGIMES:
        raise ValueError(f"regime must be one of {sorted(VALID_REGIMES)}, got {regime!r}")
    if year != 2026:
        raise ValueError("Only year=2026 (AY 2026-27 / FY 2025-26) is available in this version")

    if regime == "old":
        # Stub: old regime requires individual deduction inputs (80C, 80D, HRA, etc.)
        # Return a basic calculation without deductions — caller should compute
        # taxable income after deductions and pass it as gross_income.
        std_deduction = 50_000.0  # old regime standard deduction for salaried
        taxable = max(0.0, gross_income - std_deduction)
        # Old regime brackets (FY 2025-26): nil to 2.5L, 5% 2.5-5L, 20% 5-10L, 30% above 10L
        old_brackets = [
            (250_000, 0.00),
            (500_000, 0.05),
            (1_000_000, 0.20),
            (float("inf"), 0.30),
        ]
        breakdown: List[INBracketDetail] = []
        tax_gross = 0.0
        prev = 0.0
        marginal = 0.0
        for bound, rate in old_brackets:
            if taxable <= prev:
                break
            chunk = min(taxable, bound) - prev
            if chunk <= 0:
                prev = bound
                continue
            t = chunk * rate
            tax_gross += t
            breakdown.append(INBracketDetail(rate=rate, taxed_in_bracket=chunk, tax_in_bracket=t))
            marginal = rate
            prev = bound
        rebate = min(tax_gross, 12_500.0) if taxable <= 500_000 else 0.0
        tax_after = max(0.0, tax_gross - rebate)
        cess = tax_after * CESS_RATE
        total = tax_after + cess
        eff = total / gross_income if gross_income > 0 else 0.0
        return INIncomeTaxResult(
            gross_income=gross_income,
            regime="old",
            year=year,
            standard_deduction=std_deduction,
            taxable_income=taxable,
            tax_before_rebate=tax_gross,
            rebate_87a=rebate,
            tax_after_rebate=tax_after,
            health_education_cess=cess,
            tax_owed=total,
            effective_rate=eff,
            marginal_rate=marginal,
            bracket_breakdown=tuple(breakdown),
        )

    # New regime
    std_deduction = STANDARD_DEDUCTION_NEW
    taxable = max(0.0, gross_income - std_deduction)

    breakdown = []
    tax_gross = 0.0
    prev = 0.0
    marginal_rate = 0.0

    for bound, rate in _NEW_REGIME_BRACKETS:
        if taxable <= prev:
            break
        chunk = min(taxable, bound) - prev
        if chunk <= 0:
            prev = bound
            continue
        t = chunk * rate
        tax_gross += t
        breakdown.append(INBracketDetail(rate=rate, taxed_in_bracket=chunk, tax_in_bracket=t))
        marginal_rate = rate
        prev = bound

    # Section 87A rebate
    if taxable <= REBATE_87A_INCOME_LIMIT:
        rebate = min(tax_gross, REBATE_87A_MAX)
    else:
        rebate = 0.0

    tax_after_rebate = max(0.0, tax_gross - rebate)
    cess = tax_after_rebate * CESS_RATE
    tax_total = tax_after_rebate + cess

    effective_rate = tax_total / gross_income if gross_income > 0 else 0.0

    return INIncomeTaxResult(
        gross_income=gross_income,
        regime=regime,
        year=year,
        standard_deduction=std_deduction,
        taxable_income=taxable,
        tax_before_rebate=tax_gross,
        rebate_87a=rebate,
        tax_after_rebate=tax_after_rebate,
        health_education_cess=cess,
        tax_owed=tax_total,
        effective_rate=effective_rate,
        marginal_rate=marginal_rate,
        bracket_breakdown=tuple(breakdown),
    )
