"""UK income tax + National Insurance calculator for 2025/26 tax year.

Reported as 2026 assessment year per project convention.

Personal allowance taper:
    For income above £100,000 the personal allowance is reduced by £1 for every
    £2 of income over £100,000. It reaches zero when income exceeds £125,140.

Reference: HMRC for 2025/26 rates and thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# 2025/26 UK tax constants
# ---------------------------------------------------------------------------
PERSONAL_ALLOWANCE = 12_570.0
BASIC_RATE = 0.20          # up to £37,700 above allowance
HIGHER_RATE = 0.40         # £37,701–£125,140 total income
ADDITIONAL_RATE = 0.45     # above £125,140

BASIC_RATE_BAND = 37_700.0          # width of basic-rate band
ADDITIONAL_RATE_THRESHOLD = 125_140.0

# National Insurance thresholds (employee Class 1)
NI_LOWER = 12_570.0         # Primary Threshold
NI_UPPER = 50_270.0         # Upper Earnings Limit
NI_RATE_MAIN = 0.08         # 8% on earnings between Lower and Upper
NI_RATE_UPPER = 0.02        # 2% above Upper


@dataclass(frozen=True)
class UKBracketDetail:
    """Single income-tax band contribution."""
    name: str
    rate: float
    income_in_band: float
    tax_in_band: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "rate": self.rate,
            "income_in_band": round(self.income_in_band, 2),
            "tax_in_band": round(self.tax_in_band, 2),
        }


@dataclass(frozen=True)
class UKIncomeTaxResult:
    """Result of a UK income tax + National Insurance calculation."""
    gross_income: float
    year: int
    personal_allowance_used: float
    taxable_income: float
    income_tax: float
    national_insurance: float
    total_tax: float
    effective_rate: float
    take_home: float
    bracket_breakdown: tuple  # tuple of UKBracketDetail

    def to_dict(self) -> dict:
        return {
            "gross_income": round(self.gross_income, 2),
            "year": self.year,
            "personal_allowance_used": round(self.personal_allowance_used, 2),
            "taxable_income": round(self.taxable_income, 2),
            "income_tax": round(self.income_tax, 2),
            "national_insurance": round(self.national_insurance, 2),
            "total_tax": round(self.total_tax, 2),
            "effective_rate": round(self.effective_rate, 6),
            "take_home": round(self.take_home, 2),
            "bracket_breakdown": [b.to_dict() for b in self.bracket_breakdown],
        }


def calculate(income: float, year: int = 2026) -> UKIncomeTaxResult:
    """Compute UK income tax and employee National Insurance for 2025/26.

    Personal allowance taper (income > £100,000):
        effective_allowance = max(0, PERSONAL_ALLOWANCE - (income - 100_000) / 2)

    Income tax bands (applied to income above effective personal allowance):
        Basic rate  20%: up to £37,700
        Higher rate 40%: £37,701 to £125,140 total income
        Additional  45%: above £125,140 total income

    NI Class 1 employee rates:
        8%  on earnings £12,570–£50,270
        2%  on earnings above £50,270

    Args:
        income: Gross annual income in GBP.
        year: Tax year — only 2025/26 (reported as 2026) is encoded.

    Returns:
        UKIncomeTaxResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(30_000)
        >>> round(r.income_tax, 2)
        3486.0
    """
    if income < 0:
        raise ValueError("income must be >= 0")
    if year != 2026:
        raise ValueError("Only year=2026 (tax year 2025/26) is available in this version")

    # Personal allowance — taper above £100K
    taper_threshold = 100_000.0
    if income > taper_threshold:
        reduction = (income - taper_threshold) / 2.0
        pa = max(0.0, PERSONAL_ALLOWANCE - reduction)
    else:
        pa = PERSONAL_ALLOWANCE

    taxable = max(0.0, income - pa)

    # Income tax bands
    breakdown: List[UKBracketDetail] = []
    it = 0.0

    # Basic rate band
    basic_chunk = min(taxable, BASIC_RATE_BAND)
    if basic_chunk > 0:
        t = basic_chunk * BASIC_RATE
        it += t
        breakdown.append(UKBracketDetail("basic", BASIC_RATE, basic_chunk, t))

    # Higher rate band — between basic_rate_band and additional_rate_threshold
    # The threshold is measured against total income
    # Higher rate applies on taxable income from BASIC_RATE_BAND up to
    # (ADDITIONAL_RATE_THRESHOLD - pa) in taxable terms
    higher_upper_taxable = ADDITIONAL_RATE_THRESHOLD - pa
    higher_chunk = max(0.0, min(taxable, higher_upper_taxable) - BASIC_RATE_BAND)
    if higher_chunk > 0:
        t = higher_chunk * HIGHER_RATE
        it += t
        breakdown.append(UKBracketDetail("higher", HIGHER_RATE, higher_chunk, t))

    # Additional rate
    addl_chunk = max(0.0, taxable - higher_upper_taxable)
    if addl_chunk > 0:
        t = addl_chunk * ADDITIONAL_RATE
        it += t
        breakdown.append(UKBracketDetail("additional", ADDITIONAL_RATE, addl_chunk, t))

    # National Insurance (Class 1 employee)
    ni = 0.0
    if income > NI_LOWER:
        main_band = min(income, NI_UPPER) - NI_LOWER
        ni += main_band * NI_RATE_MAIN
    if income > NI_UPPER:
        ni += (income - NI_UPPER) * NI_RATE_UPPER

    total_tax = it + ni
    effective_rate = total_tax / income if income > 0 else 0.0
    take_home = income - total_tax

    return UKIncomeTaxResult(
        gross_income=income,
        year=year,
        personal_allowance_used=pa,
        taxable_income=taxable,
        income_tax=it,
        national_insurance=ni,
        total_tax=total_tax,
        effective_rate=effective_rate,
        take_home=take_home,
        bracket_breakdown=tuple(breakdown),
    )
