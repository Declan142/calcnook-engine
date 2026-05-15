"""India GST (Goods & Services Tax) calculator.

Statutory framework:
    - Central Goods and Services Tax Act, 2017 (CGST).
    - State Goods and Services Tax Acts, 2017 (SGST).
    - Integrated Goods and Services Tax Act, 2017 (IGST).

Standard slab rates (post-GST-Council framework):
    0% (exempt) | 5% | 12% | 18% | 28%
Plus a Compensation Cess on luxury & sin goods (not modelled here).

Breakup:
    - Intra-state supply: CGST (½ rate) + SGST (½ rate). Both flow to the
      respective central / state coffers.
    - Inter-state supply: IGST (full rate). Centre apportions to destination
      state under the GST settlement mechanism.

This module supports:
    - ex-tax (exclusive) and gross (inclusive) input amounts.
    - Rate accepted as decimal (0.18) OR percent (18.0); auto-detected.
"""

from __future__ import annotations

from dataclasses import dataclass


# Valid GST slabs (decimal). Compensation cess slabs not modelled.
_VALID_RATES_PCT = (0.0, 5.0, 12.0, 18.0, 28.0)
VALID_BREAKUPS = frozenset({"cgst_sgst", "igst"})


@dataclass(frozen=True)
class GSTResult:
    """Result of a GST computation."""
    base: float
    gst_total: float
    total: float
    cgst: float
    sgst: float
    igst: float
    rate_pct: float
    breakup: str
    is_inclusive: bool

    def to_dict(self) -> dict:
        return {
            "base": round(self.base, 2),
            "gst_total": round(self.gst_total, 2),
            "total": round(self.total, 2),
            "cgst": round(self.cgst, 2),
            "sgst": round(self.sgst, 2),
            "igst": round(self.igst, 2),
            "rate_pct": self.rate_pct,
            "breakup": self.breakup,
            "is_inclusive": self.is_inclusive,
        }


def _normalise_rate(rate: float) -> tuple[float, float]:
    """Return (rate_decimal, rate_pct) given input as either decimal or percent.

    Auto-detect: rate >= 1.0 → treated as percent.
    """
    if rate < 0:
        raise ValueError("rate must be >= 0")
    if rate >= 1.0:
        rate_pct = float(rate)
        rate_decimal = rate_pct / 100.0
    else:
        rate_decimal = float(rate)
        rate_pct = rate_decimal * 100.0

    # Validate against permitted slabs
    if not any(abs(rate_pct - v) < 1e-6 for v in _VALID_RATES_PCT):
        raise ValueError(
            f"GST rate {rate_pct}% not in permitted slabs "
            f"{_VALID_RATES_PCT}"
        )
    return rate_decimal, rate_pct


def calculate(
    amount: float,
    rate: float,
    is_inclusive: bool = False,
    breakup: str = "cgst_sgst",
) -> GSTResult:
    """Compute GST on a transaction.

    Args:
        amount: Monetary amount in INR.
        rate: GST rate as decimal (0.18) OR percent (18.0). Auto-detected:
            ``rate >= 1.0`` → percent. Must equal one of {0, 5, 12, 18, 28}%.
        is_inclusive: If True, ``amount`` already includes GST and we extract
            ``base = amount / (1 + rate)``. Else ``base = amount`` and GST is
            added on top.
        breakup: ``"cgst_sgst"`` (intra-state, half-half) or ``"igst"``
            (inter-state, full).

    Returns:
        GSTResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(amount=1000, rate=18, breakup="cgst_sgst")
        >>> r.gst_total
        180.0
        >>> r.cgst
        90.0
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")
    if breakup not in VALID_BREAKUPS:
        raise ValueError(
            f"breakup must be one of {sorted(VALID_BREAKUPS)}, got {breakup!r}"
        )

    rate_decimal, rate_pct = _normalise_rate(rate)

    if is_inclusive:
        base = amount / (1.0 + rate_decimal) if (1.0 + rate_decimal) > 0 else amount
        gst_total = amount - base
        total = amount
    else:
        base = amount
        gst_total = base * rate_decimal
        total = base + gst_total

    if breakup == "cgst_sgst":
        cgst = gst_total / 2.0
        sgst = gst_total / 2.0
        igst = 0.0
    else:  # igst
        cgst = 0.0
        sgst = 0.0
        igst = gst_total

    return GSTResult(
        base=base,
        gst_total=gst_total,
        total=total,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        rate_pct=rate_pct,
        breakup=breakup,
        is_inclusive=is_inclusive,
    )
