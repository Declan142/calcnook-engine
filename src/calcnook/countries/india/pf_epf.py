"""India PF / EPF (Employees' Provident Fund) calculator.

Statutory backing:
    - Employees' Provident Funds and Miscellaneous Provisions Act, 1952.
    - EPF Scheme 1952; EPS (Employees' Pension Scheme) 1995.

Standard contribution structure:
    - Employee contribution: 12% of basic + DA.
    - Employer contribution: 12% of basic + DA, split as
        * 8.33% to EPS (Pension), capped at ₹15,000 wage ceiling per EPFO rule.
        * 3.67% to EPF (Provident Fund).

Wage ceiling for the employer's EPS share is ₹15,000 (EPFO 2014 notification).
Employee may contribute on actual wages (no ceiling) under voluntary
basis-extension allowed by Para 26(6); we follow the common payroll convention
where employee % is applied to actual basic and the ₹15K cap only restrains the
employer's share unless caller overrides via ``basic_cap``.

Future value: monthly contributions are compounded at the supplied annual rate
using the standard SIP formula (ordinary annuity, end-of-period contribution),
delegated to ``calcnook.core.periodic_investment.calculate``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core import periodic_investment


# EPF/EPS split (employer portion, % of basic):
EPS_SHARE_PCT = 0.0833       # 8.33% to Employees' Pension Scheme
EPF_SHARE_PCT = 0.0367       # 3.67% to EPF (employer contribution)
DEFAULT_BASIC_CAP = 15_000.0 # EPFO ₹15K wage ceiling for employer EPS share
DEFAULT_EMPLOYEE_PCT = 0.12
DEFAULT_EMPLOYER_PCT = 0.12
DEFAULT_ANNUAL_RETURN = 0.08


@dataclass(frozen=True)
class PFEPFResult:
    """Result of an EPF / EPS contribution and corpus projection."""
    monthly_basic: float
    employee_pct: float
    employer_pct: float
    years: float
    annual_return: float
    basic_cap: float
    employee_monthly: float
    employer_monthly: float
    employer_eps_monthly: float
    employer_epf_monthly: float
    total_monthly: float
    corpus_at_retirement: float
    breakdown: dict

    def to_dict(self) -> dict:
        return {
            "monthly_basic": round(self.monthly_basic, 2),
            "employee_pct": self.employee_pct,
            "employer_pct": self.employer_pct,
            "years": self.years,
            "annual_return": self.annual_return,
            "basic_cap": self.basic_cap,
            "employee_monthly": round(self.employee_monthly, 2),
            "employer_monthly": round(self.employer_monthly, 2),
            "employer_eps_monthly": round(self.employer_eps_monthly, 2),
            "employer_epf_monthly": round(self.employer_epf_monthly, 2),
            "total_monthly": round(self.total_monthly, 2),
            "corpus_at_retirement": round(self.corpus_at_retirement, 2),
            "breakdown": self.breakdown,
        }


def calculate(
    monthly_basic: float,
    years: float,
    employee_pct: float = DEFAULT_EMPLOYEE_PCT,
    employer_pct: float = DEFAULT_EMPLOYER_PCT,
    annual_return: float = DEFAULT_ANNUAL_RETURN,
    basic_cap: float = DEFAULT_BASIC_CAP,
) -> PFEPFResult:
    """Compute PF/EPF monthly contributions and projected retirement corpus.

    The employer's contribution is split per EPFO rules:
        - 8.33% (of capped basic) → EPS (Pension Scheme)
        - 3.67% (of capped basic) → EPF (Provident Fund)

    The ``basic_cap`` (default ₹15,000) caps only the employer's share. The
    employee contribution applies to the actual basic by default — most payroll
    systems follow this convention.

    Future-value projection compounds the **EPF** portion of contributions
    (employee_monthly + employer_epf_monthly) at ``annual_return``. The EPS
    portion is excluded from the corpus because it funds a defined-benefit
    pension, not a lump-sum. (If you want both included, pass ``employer_pct``
    so that the full employer share routes to EPF only — i.e. set ``basic_cap``
    very high and treat the engine output's ``corpus_at_retirement`` as
    "EPF + voluntary EPS-replacement corpus".)

    Args:
        monthly_basic: Monthly basic salary (incl. dearness allowance) in INR.
        years: Years until withdrawal / retirement.
        employee_pct: Employee contribution as decimal of basic. Default 0.12.
        employer_pct: Employer contribution as decimal of basic. Default 0.12.
        annual_return: Decimal annual EPF return (current ~8.25%, default 0.08).
        basic_cap: Wage ceiling for the employer's EPS share in INR.
            Default ₹15,000 per EPFO 2014 notification.

    Returns:
        PFEPFResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(monthly_basic=50_000, years=30)
        >>> r.employee_monthly       # 12% × ₹50K
        6000.0
        >>> r.employer_eps_monthly   # 8.33% × ₹15K (capped)
        1249.5
    """
    if monthly_basic < 0:
        raise ValueError("monthly_basic must be >= 0")
    if years < 0:
        raise ValueError("years must be >= 0")
    if employee_pct < 0 or employer_pct < 0:
        raise ValueError("employee_pct / employer_pct must be >= 0")
    if annual_return < 0:
        raise ValueError("annual_return must be >= 0")
    if basic_cap < 0:
        raise ValueError("basic_cap must be >= 0")

    capped_basic_for_employer = min(monthly_basic, basic_cap)

    employee_monthly = monthly_basic * employee_pct
    employer_monthly = capped_basic_for_employer * employer_pct

    # Standard split of employer's share when total is 12%.
    # We allocate the same split ratio (8.33 / 12 → EPS, 3.67 / 12 → EPF) when
    # employer_pct is non-zero, so a non-default employer_pct still splits
    # proportionally between EPS and EPF.
    if employer_pct > 0:
        eps_fraction_of_employer = EPS_SHARE_PCT / DEFAULT_EMPLOYER_PCT  # 8.33/12
        epf_fraction_of_employer = EPF_SHARE_PCT / DEFAULT_EMPLOYER_PCT  # 3.67/12
    else:
        eps_fraction_of_employer = 0.0
        epf_fraction_of_employer = 0.0

    employer_eps_monthly = employer_monthly * eps_fraction_of_employer
    employer_epf_monthly = employer_monthly * epf_fraction_of_employer
    total_monthly = employee_monthly + employer_monthly

    # Corpus projection: EPF portion only (employee + employer-EPF).
    # EPS funds a pension; we exclude it from lump-sum corpus.
    epf_monthly_for_corpus = employee_monthly + employer_epf_monthly
    fv_result = periodic_investment.calculate(
        monthly_amount=epf_monthly_for_corpus,
        annual_return=annual_return,
        years=years,
    )
    corpus = fv_result.future_value

    breakdown = {
        "employee_basis": "12% of actual basic (may exceed ₹15K cap)",
        "employer_basis": f"12% of min(basic, ₹{basic_cap:,.0f}) split 8.33% EPS + 3.67% EPF",
        "epf_corpus_basis": "employee + employer_epf compounded at annual_return; EPS excluded",
        "monthly_to_epf_corpus": round(epf_monthly_for_corpus, 2),
        "total_invested": round(fv_result.total_invested, 2),
        "wealth_gained": round(fv_result.wealth_gained, 2),
    }

    return PFEPFResult(
        monthly_basic=monthly_basic,
        employee_pct=employee_pct,
        employer_pct=employer_pct,
        years=years,
        annual_return=annual_return,
        basic_cap=basic_cap,
        employee_monthly=employee_monthly,
        employer_monthly=employer_monthly,
        employer_eps_monthly=employer_eps_monthly,
        employer_epf_monthly=employer_epf_monthly,
        total_monthly=total_monthly,
        corpus_at_retirement=corpus,
        breakdown=breakdown,
    )
