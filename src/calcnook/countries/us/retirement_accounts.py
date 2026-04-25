"""US retirement account calculators for 2026.

Covers 401(k) traditional pre-tax and Roth IRA with MAGI phase-out.
Contribution limits projected from 2025 + inflation adjustment.

Reference: IRS Notice 2025-xx (projected 2026 limits).
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 2026 projected contribution limits
# ---------------------------------------------------------------------------
_401K_LIMIT_UNDER_50 = 24_000
_401K_LIMIT_50_PLUS = 32_000        # includes $8K catch-up
_401K_TOTAL_LIMIT = 70_000          # combined employee + employer
_ROTH_LIMIT_UNDER_50 = 7_000
_ROTH_LIMIT_50_PLUS = 8_000         # $1K catch-up for 50+

# Roth IRA MAGI phase-out ranges 2026 (projected from 2025 + ~3%)
_ROTH_PHASEOUT = {
    "single": (150_000, 165_000),
    "married_jointly": (236_000, 246_000),
    "married_separately": (0, 10_000),       # always near-full phase-out
    "head_of_household": (150_000, 165_000),
}


@dataclass(frozen=True)
class Traditional401kResult:
    """Result of a traditional 401(k) contribution analysis."""
    employee_contribution: float
    employer_contribution: float
    total_contribution: float
    employee_limit: float
    total_limit: float
    is_employee_maxed: bool
    is_total_maxed: bool
    tax_savings_now: float          # estimated immediate tax savings (marginal bracket)
    marginal_rate_used: float
    age: int

    def to_dict(self) -> dict:
        return {
            "employee_contribution": round(self.employee_contribution, 2),
            "employer_contribution": round(self.employer_contribution, 2),
            "total_contribution": round(self.total_contribution, 2),
            "employee_limit": self.employee_limit,
            "total_limit": self.total_limit,
            "is_employee_maxed": self.is_employee_maxed,
            "is_total_maxed": self.is_total_maxed,
            "tax_savings_now": round(self.tax_savings_now, 2),
            "marginal_rate_used": self.marginal_rate_used,
            "age": self.age,
        }


@dataclass(frozen=True)
class RothIRAResult:
    """Result of a Roth IRA contribution eligibility check."""
    requested_contribution: float
    effective_contribution: float   # after phase-out
    contribution_limit: float
    phase_out_factor: float         # 1.0 = fully eligible, 0.0 = fully phased out
    magi: float
    filing_status: str
    age: int
    phase_out_low: float
    phase_out_high: float

    def to_dict(self) -> dict:
        return {
            "requested_contribution": round(self.requested_contribution, 2),
            "effective_contribution": round(self.effective_contribution, 2),
            "contribution_limit": self.contribution_limit,
            "phase_out_factor": round(self.phase_out_factor, 6),
            "magi": round(self.magi, 2),
            "filing_status": self.filing_status,
            "age": self.age,
            "phase_out_low": self.phase_out_low,
            "phase_out_high": self.phase_out_high,
        }


def traditional_401k(
    contribution: float,
    salary: float,
    employer_match_percent: float,
    employer_match_cap: float,
    age: int,
    marginal_tax_rate: float = 0.22,
) -> Traditional401kResult:
    """Analyse a traditional (pre-tax) 401(k) contribution for 2026.

    The contribution is capped at the employee elective deferral limit.
    Employer match is computed as ``employer_match_percent`` of salary up to
    ``employer_match_cap`` percent of salary (e.g. 50% match up to 6% of salary).
    Combined employee + employer is capped at the §415 total limit ($70K in 2026).

    Tax savings are estimated using the supplied ``marginal_tax_rate`` on the
    employee contribution (pre-tax deferral reduces W-2 income by that amount).

    Args:
        contribution: Employee's desired annual contribution in USD.
        salary: Employee's annual gross salary.
        employer_match_percent: Employer matches this fraction of employee contribution
            (e.g. 0.50 = 50-cent-per-dollar match).
        employer_match_cap: Employer match applies only up to this % of salary
            (e.g. 0.06 = up to 6% of salary is matched).
        age: Employee's age — determines catch-up contribution eligibility (50+).
        marginal_tax_rate: Estimated marginal federal rate for tax savings calc.

    Returns:
        Traditional401kResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = traditional_401k(10_000, 80_000, 0.50, 0.06, 35, 0.22)
        >>> r.employer_contribution
        2400.0
    """
    if contribution < 0:
        raise ValueError("contribution must be >= 0")
    if salary < 0:
        raise ValueError("salary must be >= 0")
    if not 0 <= employer_match_percent <= 1:
        raise ValueError("employer_match_percent must be between 0 and 1")
    if not 0 <= employer_match_cap <= 1:
        raise ValueError("employer_match_cap must be between 0 and 1")
    if age < 0:
        raise ValueError("age must be >= 0")
    if not 0 <= marginal_tax_rate < 1:
        raise ValueError("marginal_tax_rate must be between 0 and 1")

    employee_limit = _401K_LIMIT_50_PLUS if age >= 50 else _401K_LIMIT_UNDER_50
    employee_contrib = min(contribution, employee_limit)

    # Employer match: match_pct of employee contrib, up to match_cap% of salary
    matchable_salary = salary * employer_match_cap
    employer_contrib = min(employee_contrib * employer_match_percent, matchable_salary * employer_match_percent)
    # Actually: employer matches employee_match_percent on each dollar up to cap
    # Standard interpretation: employer contributes match_pct * min(employee_contrib, match_cap * salary)
    employer_contrib = employer_match_percent * min(employee_contrib, salary * employer_match_cap)

    total = employee_contrib + employer_contrib
    if total > _401K_TOTAL_LIMIT:
        # Reduce employer to stay within total limit
        employer_contrib = _401K_TOTAL_LIMIT - employee_contrib
        total = _401K_TOTAL_LIMIT

    tax_savings = employee_contrib * marginal_tax_rate

    return Traditional401kResult(
        employee_contribution=employee_contrib,
        employer_contribution=employer_contrib,
        total_contribution=total,
        employee_limit=float(employee_limit),
        total_limit=float(_401K_TOTAL_LIMIT),
        is_employee_maxed=(employee_contrib >= employee_limit),
        is_total_maxed=(total >= _401K_TOTAL_LIMIT),
        tax_savings_now=tax_savings,
        marginal_rate_used=marginal_tax_rate,
        age=age,
    )


def roth_ira(
    contribution: float,
    age: int,
    magi: float,
    filing_status: str = "single",
) -> RothIRAResult:
    """Check Roth IRA contribution eligibility and phase-out for 2026.

    Contribution is capped at the annual limit (age-dependent) and reduced
    pro-rata within the MAGI phase-out range. Above the phase-out upper bound,
    direct Roth IRA contributions are not allowed (phase_out_factor = 0).

    MAGI phase-out ranges 2026 (projected):
    - Single / HoH: $150,000 – $165,000
    - Married filing jointly: $236,000 – $246,000
    - Married filing separately: $0 – $10,000

    Args:
        contribution: Desired contribution amount.
        age: Contributor's age — determines limit ($7K under 50, $8K 50+).
        magi: Modified Adjusted Gross Income.
        filing_status: One of the four standard filing statuses.

    Returns:
        RothIRAResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = roth_ira(7_000, 30, 157_500, "single")
        >>> round(r.phase_out_factor, 4)
        0.5
    """
    if contribution < 0:
        raise ValueError("contribution must be >= 0")
    if age < 0:
        raise ValueError("age must be >= 0")
    if magi < 0:
        raise ValueError("magi must be >= 0")
    if filing_status not in _ROTH_PHASEOUT:
        raise ValueError(f"filing_status must be one of {sorted(_ROTH_PHASEOUT)}, got {filing_status!r}")

    limit = _ROTH_LIMIT_50_PLUS if age >= 50 else _ROTH_LIMIT_UNDER_50
    capped = min(contribution, limit)

    low, high = _ROTH_PHASEOUT[filing_status]
    phaseout_range = high - low

    if magi <= low:
        factor = 1.0
    elif magi >= high:
        factor = 0.0
    else:
        factor = 1.0 - (magi - low) / phaseout_range

    effective = capped * factor

    return RothIRAResult(
        requested_contribution=contribution,
        effective_contribution=effective,
        contribution_limit=float(limit),
        phase_out_factor=factor,
        magi=magi,
        filing_status=filing_status,
        age=age,
        phase_out_low=float(low),
        phase_out_high=float(high),
    )
