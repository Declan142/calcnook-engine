"""Mudarabah — profit-sharing investment (Sharia fixed-deposit alternative).

The investor (rabb-ul-mal) provides capital; the fund manager (mudarib)
provides expertise and labour. Profit is split according to a pre-agreed ratio.
Loss (if any) is borne entirely by the investor; the manager loses time/effort
but not capital.

Cross-cutting module: currency-agnostic, no country specifics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MudarabahResult:
    capital: float
    actual_profit_amount: float
    investor_share_ratio: float
    investor_profit: float
    manager_profit: float
    investor_total: float
    years: Optional[float]
    annualised_return: Optional[float]  # None if years not provided

    def to_dict(self) -> dict:
        d: dict = {
            "capital": round(self.capital, 2),
            "actual_profit_amount": round(self.actual_profit_amount, 2),
            "investor_share_ratio": self.investor_share_ratio,
            "investor_profit": round(self.investor_profit, 2),
            "manager_profit": round(self.manager_profit, 2),
            "investor_total": round(self.investor_total, 2),
            "years": self.years,
            "annualised_return": (
                round(self.annualised_return, 6)
                if self.annualised_return is not None
                else None
            ),
        }
        return d


def calculate(
    capital: float,
    actual_profit_amount: float,
    investor_share_ratio: float,
    years: Optional[float] = None,
) -> MudarabahResult:
    """Compute Mudarabah profit-sharing split between investor and manager.

    In a profit scenario the surplus is divided per ``investor_share_ratio``.
    In a loss scenario (``actual_profit_amount < 0``) the full loss is borne by
    the investor; the manager receives zero profit.

    Args:
        capital: Initial capital provided by the investor. Must be > 0.
        actual_profit_amount: Realised profit (positive) or loss (negative) on
            the venture. A loss value reduces the investor's principal.
        investor_share_ratio: Fraction of profit allocated to the investor,
            expressed as a decimal in (0, 1]. E.g. 0.7 = 70 % investor share.
            Must be in (0, 1].
        years: Optional investment horizon in years used to compute an
            annualised return. Must be > 0 if provided.

    Returns:
        MudarabahResult with profit split and optional annualised return.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(100_000, 20_000, 0.70, years=3)
        >>> round(r.investor_profit, 2)
        14000.0
        >>> round(r.manager_profit, 2)
        6000.0
    """
    if capital <= 0:
        raise ValueError("capital must be > 0")
    if not (0 < investor_share_ratio <= 1):
        raise ValueError("investor_share_ratio must be in (0, 1]")
    if years is not None and years <= 0:
        raise ValueError("years must be > 0 when provided")

    if actual_profit_amount >= 0:
        # Profit scenario — split per agreed ratio
        investor_profit = actual_profit_amount * investor_share_ratio
        manager_profit = actual_profit_amount * (1 - investor_share_ratio)
    else:
        # Loss scenario — full loss borne by investor; manager earns nothing
        investor_profit = actual_profit_amount  # negative
        manager_profit = 0.0

    investor_total = capital + investor_profit

    annualised_return: Optional[float] = None
    if years is not None:
        # CAGR: (investor_total / capital)^(1/years) - 1
        ratio = investor_total / capital
        if ratio > 0:
            annualised_return = ratio ** (1.0 / years) - 1.0
        else:
            # Total loss of capital or worse — return undefined (set to -1 floor)
            annualised_return = -1.0

    return MudarabahResult(
        capital=capital,
        actual_profit_amount=actual_profit_amount,
        investor_share_ratio=investor_share_ratio,
        investor_profit=investor_profit,
        manager_profit=manager_profit,
        investor_total=investor_total,
        years=years,
        annualised_return=annualised_return,
    )
