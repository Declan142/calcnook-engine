"""Retirement planning — corpus needed, monthly contribution, safe withdrawal.

Universal calculation. No country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Corpus needed
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CorpusNeededResult:
    annual_expense: float
    years_in_retirement: int
    post_retirement_return: float
    inflation: float
    corpus_needed: float

    def to_dict(self) -> dict:
        return {
            "annual_expense": round(self.annual_expense, 2),
            "years_in_retirement": self.years_in_retirement,
            "post_retirement_return": self.post_retirement_return,
            "inflation": self.inflation,
            "corpus_needed": round(self.corpus_needed, 2),
        }


def corpus_needed(
    annual_expense: float,
    years_in_retirement: int,
    post_retirement_return: float,
    inflation: float,
) -> CorpusNeededResult:
    """Calculate the lump-sum corpus required to sustain a given annual expense.

    Uses the present value of an inflation-adjusted annuity. The real rate of
    return is approximated as: real_rate = (1 + post_retirement_return) /
    (1 + inflation) - 1.

    If real_rate == 0 (return equals inflation), corpus = annual_expense * years.

    Args:
        annual_expense: Annual spending need in today's money. Must be > 0.
        years_in_retirement: Number of years in retirement. Must be >= 1.
        post_retirement_return: Decimal annual nominal return during retirement,
            e.g. 0.07 for 7%.
        inflation: Decimal annual inflation rate, e.g. 0.06 for 6%.

    Returns:
        CorpusNeededResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = corpus_needed(50_000, 30, 0.07, 0.06)
        >>> round(r.corpus_needed, 0)
        1415096.0
    """
    if annual_expense <= 0:
        raise ValueError("annual_expense must be > 0")
    if years_in_retirement < 1:
        raise ValueError("years_in_retirement must be >= 1")
    if post_retirement_return < 0:
        raise ValueError("post_retirement_return must be >= 0")
    if inflation < 0:
        raise ValueError("inflation must be >= 0")

    real_rate = (1 + post_retirement_return) / (1 + inflation) - 1

    if abs(real_rate) < 1e-10:
        corpus = annual_expense * years_in_retirement
    else:
        # PV of growing annuity (real terms) — each withdrawal is in today's money
        corpus = annual_expense * (1 - (1 + real_rate) ** (-years_in_retirement)) / real_rate

    return CorpusNeededResult(
        annual_expense=annual_expense,
        years_in_retirement=years_in_retirement,
        post_retirement_return=post_retirement_return,
        inflation=inflation,
        corpus_needed=corpus,
    )


# ---------------------------------------------------------------------------
# Monthly contribution needed to reach corpus
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MonthlyContributionResult:
    target_corpus: float
    years_to_retirement: int
    annual_return: float
    current_savings: float
    monthly_contribution: float

    def to_dict(self) -> dict:
        return {
            "target_corpus": round(self.target_corpus, 2),
            "years_to_retirement": self.years_to_retirement,
            "annual_return": self.annual_return,
            "current_savings": round(self.current_savings, 2),
            "monthly_contribution": round(self.monthly_contribution, 2),
        }


def monthly_contribution_for(
    target_corpus: float,
    years_to_retirement: int,
    annual_return: float,
    current_savings: float = 0.0,
) -> MonthlyContributionResult:
    """Calculate the monthly SIP contribution needed to reach a retirement corpus.

    Accounts for existing savings that will also compound until retirement.
    Uses the ordinary annuity (end-of-period) SIP formula solved for P:
        P = (FV_needed) * r / ((1+r)^n - 1) / (1+r)
    where FV_needed = target - FV of current savings.

    Args:
        target_corpus: Desired retirement corpus. Must be > 0.
        years_to_retirement: Years until retirement. Must be >= 1.
        annual_return: Decimal expected annual return, e.g. 0.12 for 12%.
        current_savings: Existing savings that will compound. Default 0.

    Returns:
        MonthlyContributionResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = monthly_contribution_for(10_000_000, 20, 0.12)
        >>> round(r.monthly_contribution, 2)
        10109.21
    """
    if target_corpus <= 0:
        raise ValueError("target_corpus must be > 0")
    if years_to_retirement < 1:
        raise ValueError("years_to_retirement must be >= 1")
    if annual_return < 0:
        raise ValueError("annual_return must be >= 0")
    if current_savings < 0:
        raise ValueError("current_savings must be >= 0")

    monthly_rate = annual_return / 12
    n = years_to_retirement * 12

    # FV of current savings
    if monthly_rate == 0:
        fv_savings = current_savings
    else:
        fv_savings = current_savings * (1 + monthly_rate) ** n

    remaining_corpus = max(target_corpus - fv_savings, 0.0)

    if remaining_corpus == 0:
        monthly = 0.0
    elif monthly_rate == 0:
        monthly = remaining_corpus / n
    else:
        # Solve SIP formula for P
        monthly = remaining_corpus * monthly_rate / (((1 + monthly_rate) ** n - 1) * (1 + monthly_rate))

    return MonthlyContributionResult(
        target_corpus=target_corpus,
        years_to_retirement=years_to_retirement,
        annual_return=annual_return,
        current_savings=current_savings,
        monthly_contribution=monthly,
    )


# ---------------------------------------------------------------------------
# Safe withdrawal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SafeWithdrawalResult:
    corpus: float
    withdrawal_rate: float
    annual_withdrawal: float
    monthly_withdrawal: float

    def to_dict(self) -> dict:
        return {
            "corpus": round(self.corpus, 2),
            "withdrawal_rate": self.withdrawal_rate,
            "annual_withdrawal": round(self.annual_withdrawal, 2),
            "monthly_withdrawal": round(self.monthly_withdrawal, 2),
        }


def safe_withdrawal(
    corpus: float,
    withdrawal_rate: float = 0.04,
) -> SafeWithdrawalResult:
    """Calculate annual and monthly safe withdrawal from a retirement corpus.

    Based on the 4% rule (Bengen 1994): withdraw 4% of initial corpus per year,
    adjusted each year for inflation. This function returns the raw numbers for
    the first year. Caller adjusts annually.

    Args:
        corpus: Retirement corpus (lump-sum). Must be > 0.
        withdrawal_rate: Decimal annual withdrawal rate. Default 0.04 (4% rule).
            Must be between 0 (exclusive) and 1 (inclusive).

    Returns:
        SafeWithdrawalResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = safe_withdrawal(1_000_000)
        >>> r.annual_withdrawal
        40000.0
        >>> r.monthly_withdrawal
        3333.3333333333335
    """
    if corpus <= 0:
        raise ValueError("corpus must be > 0")
    if not (0 < withdrawal_rate <= 1):
        raise ValueError("withdrawal_rate must be between 0 (exclusive) and 1 (inclusive)")

    annual = corpus * withdrawal_rate
    monthly = annual / 12

    return SafeWithdrawalResult(
        corpus=corpus,
        withdrawal_rate=withdrawal_rate,
        annual_withdrawal=annual,
        monthly_withdrawal=monthly,
    )
