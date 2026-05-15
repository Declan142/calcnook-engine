"""India Advance Tax instalment calculator — Section 211 of Income-tax Act.

Statutory backing:
    - Section 208: liability to pay advance tax if estimated tax > ₹10,000.
    - Section 211: due dates and percentages of advance tax for individuals.

Instalment schedule (FY 2024-25 / AY 2025-26 onwards, individuals):
    Q1 — by 15 Jun: 15% of total advance tax
    Q2 — by 15 Sep: 45% (cumulative) of total advance tax
    Q3 — by 15 Dec: 75% (cumulative) of total advance tax
    Q4 — by 15 Mar: 100% (cumulative) of total advance tax

Total tax for the year is computed by delegating to
``calcnook.countries.india.income_tax.calculate``. Caller may pass an existing
estimate via the same module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from . import income_tax as _income_tax


# Section 211 schedule (cumulative percentages)
INSTALMENT_SCHEDULE = [
    # (quarter_label, due_month, due_day, cumulative_pct)
    ("Q1", 6, 15, 0.15),
    ("Q2", 9, 15, 0.45),
    ("Q3", 12, 15, 0.75),
    ("Q4", 3, 15, 1.00),
]


@dataclass(frozen=True)
class InstalmentDetail:
    quarter: str
    due_date: str
    cumulative_pct: float
    cumulative_required: float
    instalment_amount: float

    def to_dict(self) -> dict:
        return {
            "quarter": self.quarter,
            "due_date": self.due_date,
            "cumulative_pct": self.cumulative_pct,
            "cumulative_required": round(self.cumulative_required, 2),
            "instalment_amount": round(self.instalment_amount, 2),
        }


@dataclass(frozen=True)
class AdvanceTaxResult:
    annual_income: float
    regime: str
    total_tax_estimated: float
    paid_so_far: float
    as_of_date: str
    current_quarter: str
    next_due_date: str | None
    next_installment_required_cumulative: float
    next_installment_due_now: float
    all_installments: tuple
    note: str | None = None

    def to_dict(self) -> dict:
        return {
            "annual_income": round(self.annual_income, 2),
            "regime": self.regime,
            "total_tax_estimated": round(self.total_tax_estimated, 2),
            "paid_so_far": round(self.paid_so_far, 2),
            "as_of_date": self.as_of_date,
            "current_quarter": self.current_quarter,
            "next_due_date": self.next_due_date,
            "next_installment_required_cumulative": round(self.next_installment_required_cumulative, 2),
            "next_installment_due_now": round(self.next_installment_due_now, 2),
            "all_installments": [i.to_dict() for i in self.all_installments],
            "note": self.note,
        }


def _financial_year_for(d: date) -> int:
    """India FY = Apr 1 to Mar 31. Returns the starting calendar year of the FY."""
    return d.year if d.month >= 4 else d.year - 1


def _instalment_due_dates(fy_start_year: int) -> List[tuple[str, date, float]]:
    """Concrete instalment dates for the FY beginning ``fy_start_year``.

    Q1, Q2, Q3 due in calendar year ``fy_start_year``.
    Q4 due in calendar year ``fy_start_year + 1`` (March 15).
    """
    out: list[tuple[str, date, float]] = []
    for label, m, d, cum in INSTALMENT_SCHEDULE:
        if m == 3:  # Q4 — March of FY-end calendar year
            due = date(fy_start_year + 1, m, d)
        else:
            due = date(fy_start_year, m, d)
        out.append((label, due, cum))
    return out


def calculate(
    annual_income: float,
    regime: str = "new",
    paid_so_far: float = 0.0,
    as_of_date: date | str | None = None,
    total_tax_for_year: float | None = None,
) -> AdvanceTaxResult:
    """Compute current advance-tax instalment due under Section 211.

    The annual tax liability is computed via
    ``calcnook.countries.india.income_tax.calculate(annual_income, regime)``
    UNLESS ``total_tax_for_year`` is supplied (caller-precomputed).

    Determines the current FY based on ``as_of_date`` (default ``date.today()``)
    and identifies the next instalment due:
        - If today is on/before Jun 15 → Q1 is next due.
        - Else if on/before Sep 15 → Q2 is next due.
        - Else if on/before Dec 15 → Q3 is next due.
        - Else if on/before Mar 15 next CY → Q4 is next due.
        - Else → no further instalments this FY (Q4 has passed).

    The "next_installment_due_now" is::

        max(0, cumulative_required_at_next_due - paid_so_far)

    Args:
        annual_income: Estimated gross annual income (INR) for the FY.
        regime: "new" (default) or "old" — passed to income_tax.calculate.
        paid_so_far: Total advance tax paid this FY so far.
        as_of_date: Reference date (default today). ISO string or date.
        total_tax_for_year: Optional caller-supplied total annual tax to skip
            the income_tax.calculate call (e.g. when caller has already
            applied non-salary-income adjustments).

    Returns:
        AdvanceTaxResult.

    Raises:
        ValueError: if any input is invalid.
    """
    if annual_income < 0:
        raise ValueError("annual_income must be >= 0")
    if paid_so_far < 0:
        raise ValueError("paid_so_far must be >= 0")

    if as_of_date is None:
        today = date.today()
    elif isinstance(as_of_date, str):
        try:
            today = date.fromisoformat(as_of_date)
        except ValueError as exc:
            raise ValueError("as_of_date must be ISO YYYY-MM-DD") from exc
    elif isinstance(as_of_date, date):
        today = as_of_date
    else:
        raise ValueError("as_of_date must be a date, ISO string, or None")

    if total_tax_for_year is not None:
        if total_tax_for_year < 0:
            raise ValueError("total_tax_for_year must be >= 0")
        total_tax = float(total_tax_for_year)
    else:
        tax_result = _income_tax.calculate(annual_income, regime=regime)
        total_tax = tax_result.tax_owed

    fy_start = _financial_year_for(today)
    schedule = _instalment_due_dates(fy_start)

    # Build all_installments details (per-instalment amount = cum × tax minus prior cum)
    details: list[InstalmentDetail] = []
    prev_cum = 0.0
    for label, due, cum in schedule:
        cum_required = cum * total_tax
        instalment = cum_required - (prev_cum * total_tax)
        details.append(InstalmentDetail(
            quarter=label,
            due_date=due.isoformat(),
            cumulative_pct=cum,
            cumulative_required=cum_required,
            instalment_amount=instalment,
        ))
        prev_cum = cum

    # Identify "current quarter" = the quarter whose due date is the next on/after today.
    next_quarter = None
    next_due_date = None
    next_cum_required = 0.0
    for label, due, cum in schedule:
        if due >= today:
            next_quarter = label
            next_due_date = due.isoformat()
            next_cum_required = cum * total_tax
            break

    note: str | None = None
    if total_tax <= 10_000.0:
        note = (
            "Total estimated tax ≤ ₹10,000 — Sec 208 advance tax not required. "
            "Schedule shown for reference only."
        )

    if next_quarter is None:
        # Past Q4 due date — FY's instalment cycle done
        return AdvanceTaxResult(
            annual_income=annual_income,
            regime=regime,
            total_tax_estimated=total_tax,
            paid_so_far=paid_so_far,
            as_of_date=today.isoformat(),
            current_quarter="POST_Q4",
            next_due_date=None,
            next_installment_required_cumulative=total_tax,
            next_installment_due_now=max(0.0, total_tax - paid_so_far),
            all_installments=tuple(details),
            note=(note or "All four advance-tax instalments for this FY have already passed; settle balance via self-assessment by Jul 31."),
        )

    next_due_now = max(0.0, next_cum_required - paid_so_far)

    return AdvanceTaxResult(
        annual_income=annual_income,
        regime=regime,
        total_tax_estimated=total_tax,
        paid_so_far=paid_so_far,
        as_of_date=today.isoformat(),
        current_quarter=next_quarter,
        next_due_date=next_due_date,
        next_installment_required_cumulative=next_cum_required,
        next_installment_due_now=next_due_now,
        all_installments=tuple(details),
        note=note,
    )
