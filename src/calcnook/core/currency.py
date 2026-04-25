"""Multi-currency math — FX conversion, formatting, lakh/crore notation.

Universal calculation. No country specifics beyond symbol/format conventions.
"""

from __future__ import annotations

from dataclasses import dataclass

# Currency symbol map — extend as needed
_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "AED": "AED ",
    "SAR": "SAR ",
    "JPY": "¥",
    "CNY": "¥",
    "CAD": "CA$",
    "AUD": "A$",
}


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConvertResult:
    amount: float
    from_currency: str
    to_currency: str
    rate_used: float
    converted_amount: float

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate_used": self.rate_used,
            "converted_amount": round(self.converted_amount, 6),
        }


def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: dict[str, float],
) -> ConvertResult:
    """Convert an amount between any two currencies using a USD-based rate dict.

    rates must map currency codes to their value per 1 USD, e.g.:
        {"USD": 1.0, "INR": 83.5, "EUR": 0.93, "AED": 3.67}

    Conversion: amount_in_USD = amount / rates[from_currency]
                result = amount_in_USD * rates[to_currency]

    Args:
        amount: Amount to convert. Must be >= 0.
        from_currency: ISO-4217 source currency code (must be in rates).
        to_currency: ISO-4217 target currency code (must be in rates).
        rates: Dict mapping currency code to units per USD.

    Returns:
        ConvertResult.

    Raises:
        ValueError: if amount < 0 or either currency is missing from rates.

    Example:
        >>> r = convert(1000, "USD", "INR", {"USD": 1.0, "INR": 83.5})
        >>> r.converted_amount
        83500.0
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")
    if from_currency not in rates:
        raise ValueError(f"'{from_currency}' not found in rates dict")
    if to_currency not in rates:
        raise ValueError(f"'{to_currency}' not found in rates dict")

    rate_from = rates[from_currency]
    rate_to = rates[to_currency]

    if rate_from <= 0:
        raise ValueError(f"rate for '{from_currency}' must be > 0")
    if rate_to <= 0:
        raise ValueError(f"rate for '{to_currency}' must be > 0")

    usd_equivalent = amount / rate_from
    converted = usd_equivalent * rate_to
    cross_rate = rate_to / rate_from

    return ConvertResult(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
        rate_used=cross_rate,
        converted_amount=converted,
    )


# ---------------------------------------------------------------------------
# format_amount
# ---------------------------------------------------------------------------

def format_amount(amount: float, currency: str) -> str:
    """Return a human-readable currency string with appropriate symbol.

    Supported currencies: USD, EUR, GBP, INR, AED, SAR, JPY, CNY, CAD, AUD.
    For JPY/CNY, no decimal places (whole yen/yuan). Others: 2 decimal places.
    Unknown currencies fall back to "{CODE} {amount:.2f}".

    Args:
        amount: Numeric amount.
        currency: ISO-4217 currency code (uppercase).

    Returns:
        Formatted string, e.g. "$1,234.56", "₹83,500.00", "¥1,500".

    Example:
        >>> format_amount(83500, "INR")
        '₹83,500.00'
        >>> format_amount(1500, "JPY")
        '¥1,500'
    """
    symbol = _SYMBOLS.get(currency)
    if currency in {"JPY", "CNY"}:
        formatted = f"{amount:,.0f}"
    else:
        formatted = f"{amount:,.2f}"

    if symbol is None:
        return f"{currency} {formatted}"
    return f"{symbol}{formatted}"


# ---------------------------------------------------------------------------
# lakh_crore_format
# ---------------------------------------------------------------------------

def lakh_crore_format(amount: float) -> str:
    """Format an INR amount using Indian lakh/crore notation.

    Thresholds:
        >= 1,00,00,000 (1 crore)  → "₹X.XX Cr"
        >= 1,00,000    (1 lakh)   → "₹X.XX L"
        < 1,00,000               → "₹{amount:,.2f}"

    Args:
        amount: Amount in INR (numeric). Must be >= 0.

    Returns:
        Formatted string in lakh/crore notation.

    Raises:
        ValueError: if amount < 0.

    Example:
        >>> lakh_crore_format(1_500_000)
        '₹15.00 L'
        >>> lakh_crore_format(25_000_000)
        '₹2.50 Cr'
        >>> lakh_crore_format(50_000)
        '₹50,000.00'
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")

    CRORE = 1_00_00_000  # 10,000,000
    LAKH = 1_00_000      # 100,000

    if amount >= CRORE:
        return f"₹{amount / CRORE:.2f} Cr"
    elif amount >= LAKH:
        return f"₹{amount / LAKH:.2f} L"
    else:
        return f"₹{amount:,.2f}"
