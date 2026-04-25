"""Saudi Arabia VAT calculator — standard rate 15%.

Royal Decree M/113 (2020) raised the Saudi VAT rate from 5% to 15%
effective 1 July 2020.
"""

from __future__ import annotations

from dataclasses import dataclass

SA_VAT_RATE = 0.15


@dataclass(frozen=True)
class SAVATResult:
    """Result of a Saudi Arabia VAT calculation."""
    vat_amount: float
    net_amount: float
    gross_amount: float
    rate: float
    is_inclusive: bool

    def to_dict(self) -> dict:
        return {
            "vat_amount": round(self.vat_amount, 2),
            "net_amount": round(self.net_amount, 2),
            "gross_amount": round(self.gross_amount, 2),
            "rate": self.rate,
            "is_inclusive": self.is_inclusive,
        }


def calculate(amount: float, is_inclusive: bool = False) -> SAVATResult:
    """Compute Saudi Arabia VAT at 15%.

    Args:
        amount: The monetary amount in SAR.
            If ``is_inclusive=True``, the amount already includes VAT (gross).
            If ``is_inclusive=False``, the amount is ex-VAT (net).
        is_inclusive: Whether VAT is already included in ``amount``.

    Returns:
        SAVATResult with vat_amount, net_amount, gross_amount.

    Raises:
        ValueError: if amount is negative.

    Example (exclusive):
        >>> r = calculate(1000, is_inclusive=False)
        >>> r.vat_amount, r.gross_amount
        (150.0, 1150.0)

    Example (inclusive):
        >>> r = calculate(1150, is_inclusive=True)
        >>> round(r.vat_amount, 4)
        150.0
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")

    if is_inclusive:
        vat = amount * SA_VAT_RATE / (1 + SA_VAT_RATE)
        net = amount - vat
        gross = amount
    else:
        vat = amount * SA_VAT_RATE
        net = amount
        gross = amount + vat

    return SAVATResult(
        vat_amount=vat,
        net_amount=net,
        gross_amount=gross,
        rate=SA_VAT_RATE,
        is_inclusive=is_inclusive,
    )
