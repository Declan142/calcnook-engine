"""UAE VAT calculator — standard rate 5%.

Federal Decree-Law No. 8 of 2017 on Value Added Tax.
Effective 1 January 2018. Standard rate: 5%.
"""

from __future__ import annotations

from dataclasses import dataclass

UAE_VAT_RATE = 0.05


@dataclass(frozen=True)
class AEVATResult:
    """Result of a UAE VAT calculation."""
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


def calculate(amount: float, is_inclusive: bool = False) -> AEVATResult:
    """Compute UAE VAT at 5%.

    Args:
        amount: The monetary amount in AED.
            If ``is_inclusive=True``, this is the VAT-inclusive (gross) price.
            If ``is_inclusive=False``, this is the net (ex-VAT) price.
        is_inclusive: Whether ``amount`` already includes VAT.

    Returns:
        AEVATResult with vat_amount, net_amount, gross_amount.

    Raises:
        ValueError: if amount is negative.

    Example (exclusive):
        >>> r = calculate(1000, is_inclusive=False)
        >>> r.vat_amount, r.gross_amount
        (50.0, 1050.0)

    Example (inclusive):
        >>> r = calculate(1050, is_inclusive=True)
        >>> round(r.vat_amount, 4)
        50.0
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")

    if is_inclusive:
        vat = amount * UAE_VAT_RATE / (1 + UAE_VAT_RATE)
        net = amount - vat
        gross = amount
    else:
        vat = amount * UAE_VAT_RATE
        net = amount
        gross = amount + vat

    return AEVATResult(
        vat_amount=vat,
        net_amount=net,
        gross_amount=gross,
        rate=UAE_VAT_RATE,
        is_inclusive=is_inclusive,
    )
