"""India Capital Gains Tax calculator — Budget 2024 (FY 2024-25 onwards).

Statutory & budget references:
    - Sections 111A (STCG on equity), 112 (LTCG general), 112A (LTCG equity).
    - Finance (No. 2) Act, 2024 — Union Budget 2024 (presented 23 Jul 2024)
      raised LTCG on equity to 12.5% (from 10%) and STCG to 20% (from 15%),
      effective 23 Jul 2024 (transactions on or after).
    - Section 50AA (debt MFs purchased on/after 1 Apr 2023): always taxed at
      slab rate, holding period irrelevant; no LTCG benefit.
    - Section 115BBH: virtual digital assets (crypto) — flat 30% regardless
      of holding period.

Holding-period thresholds (post-Budget 2024):
    - equity_listed: 12 months STCG / LTCG split
    - debt_mf:        slab rate always (post-2023 acquisition)
    - property:       24 months STCG / LTCG split
    - unlisted_equity:24 months STCG / LTCG split
    - gold:           36 months STCG / LTCG split (physical / non-financial)
    - crypto:         flat 30%, no STCG/LTCG distinction

Rates applied (LTCG):
    - equity_listed LTCG: 12.5% above ₹1,25,000 annual exemption (Sec 112A)
    - equity_listed STCG: 20% (Sec 111A)
    - property LTCG: 12.5% without indexation OR 20% with indexation (caller
      may opt-in to indexation via the ``indexation`` flag — Budget 2024 made
      this a one-time taxpayer choice for resident individuals/HUFs on
      property acquired before 23 Jul 2024)
    - debt_mf: slab rate (engine returns ``tax_payable=None`` + note)
    - crypto: flat 30%

Surcharge & cess are NOT included here — they depend on total income. The
engine emits a ``surcharge_cess_note`` reminding the caller to layer them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# Holding-period thresholds (years, before short-vs-long flip)
_THRESHOLDS_YEARS = {
    "equity_listed": 1.0,
    "debt_mf": 1.0,        # nominal — debt_mf always slab rate post-2023
    "property": 2.0,
    "unlisted_equity": 2.0,
    "gold": 3.0,
    "crypto": 0.0,         # nominal — crypto always 30%
}

VALID_ASSET_TYPES = frozenset(_THRESHOLDS_YEARS.keys())

# Rates (decimal)
EQUITY_LTCG_RATE = 0.125
EQUITY_LTCG_EXEMPTION = 1_25_000.0   # ₹1.25L annual exemption per Sec 112A
EQUITY_STCG_RATE = 0.20
PROPERTY_LTCG_NO_INDEX_RATE = 0.125
PROPERTY_LTCG_WITH_INDEX_RATE = 0.20
UNLISTED_EQUITY_LTCG_RATE = 0.125    # treated as long-term unlisted shares
GOLD_LTCG_NO_INDEX_RATE = 0.125      # post-Budget-2024, indexation withdrawn
GOLD_LTCG_WITH_INDEX_RATE = 0.20
CRYPTO_RATE = 0.30

SURCHARGE_CESS_NOTE = (
    "Surcharge (10/15/25/37%) and 4% Health & Education Cess apply on tax "
    "amount based on total taxable income — not included here."
)


@dataclass(frozen=True)
class CapitalGainsResult:
    """Result of an India capital-gains computation."""
    asset_type: str
    asset_subtype: str | None
    purchase_price: float
    sale_price: float
    purchase_date: str
    sale_date: str
    holding_period_days: int
    holding_period_years: float
    classification: str  # "STCG" | "LTCG" | "FLAT_30" | "SLAB_RATE"
    gain_amount: float
    exemption_used: float
    taxable_gain: float
    tax_payable: float | None
    indexation_used: bool
    applicable_rate: float | None
    surcharge_cess_note: str
    note: str | None

    def to_dict(self) -> dict:
        return {
            "asset_type": self.asset_type,
            "asset_subtype": self.asset_subtype,
            "purchase_price": round(self.purchase_price, 2),
            "sale_price": round(self.sale_price, 2),
            "purchase_date": self.purchase_date,
            "sale_date": self.sale_date,
            "holding_period_days": self.holding_period_days,
            "holding_period_years": round(self.holding_period_years, 4),
            "classification": self.classification,
            "gain_amount": round(self.gain_amount, 2),
            "exemption_used": round(self.exemption_used, 2),
            "taxable_gain": round(self.taxable_gain, 2),
            "tax_payable": (
                round(self.tax_payable, 2) if self.tax_payable is not None else None
            ),
            "indexation_used": self.indexation_used,
            "applicable_rate": self.applicable_rate,
            "surcharge_cess_note": self.surcharge_cess_note,
            "note": self.note,
        }


def _parse_date(label: str, value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{label} must be ISO YYYY-MM-DD, got {value!r}") from exc
    raise ValueError(f"{label} must be a date or ISO YYYY-MM-DD string, got {type(value).__name__}")


def calculate(
    asset_type: str,
    purchase_price: float,
    sale_price: float,
    purchase_date,
    sale_date,
    indexation: bool = False,
    asset_subtype: str | None = None,
) -> CapitalGainsResult:
    """Compute capital-gains tax for a single asset disposal under Budget 2024.

    Args:
        asset_type: One of ``equity_listed``, ``debt_mf``, ``property``,
            ``unlisted_equity``, ``gold``, ``crypto``.
        purchase_price: Acquisition cost in INR.
        sale_price: Realised sale consideration in INR.
        purchase_date: Date of acquisition (ISO YYYY-MM-DD or ``date``).
        sale_date: Date of sale (ISO YYYY-MM-DD or ``date``).
        indexation: If True and asset is property/gold, apply 20% LTCG with
            indexation (taxpayer choice for assets acquired before
            23 Jul 2024). Ignored for equity / debt_mf / crypto.
        asset_subtype: Optional informational tag (e.g. "house", "land",
            "physical_gold", "sgb"). Stored for reference, no tax impact.

    Returns:
        CapitalGainsResult.

    Raises:
        ValueError: if any input is invalid.

    Example:
        >>> r = calculate(
        ...     asset_type="equity_listed",
        ...     purchase_price=200_000,
        ...     sale_price=350_000,
        ...     purchase_date="2022-04-01",
        ...     sale_date="2024-09-01",
        ... )
        >>> r.classification
        'LTCG'
    """
    if asset_type not in VALID_ASSET_TYPES:
        raise ValueError(
            f"asset_type must be one of {sorted(VALID_ASSET_TYPES)}, got {asset_type!r}"
        )
    if purchase_price < 0 or sale_price < 0:
        raise ValueError("purchase_price and sale_price must be >= 0")

    pdate = _parse_date("purchase_date", purchase_date)
    sdate = _parse_date("sale_date", sale_date)

    if sdate < pdate:
        raise ValueError("sale_date must not precede purchase_date")

    days = (sdate - pdate).days
    years = days / 365.25
    gain = sale_price - purchase_price

    # ---- Crypto: flat 30%, no STCG/LTCG, no exemption, no offset (Sec 115BBH) ----
    if asset_type == "crypto":
        taxable = max(0.0, gain)
        tax = taxable * CRYPTO_RATE
        return CapitalGainsResult(
            asset_type=asset_type,
            asset_subtype=asset_subtype,
            purchase_price=purchase_price,
            sale_price=sale_price,
            purchase_date=pdate.isoformat(),
            sale_date=sdate.isoformat(),
            holding_period_days=days,
            holding_period_years=years,
            classification="FLAT_30",
            gain_amount=gain,
            exemption_used=0.0,
            taxable_gain=taxable,
            tax_payable=tax,
            indexation_used=False,
            applicable_rate=CRYPTO_RATE,
            surcharge_cess_note=SURCHARGE_CESS_NOTE,
            note="Section 115BBH: virtual digital assets taxed at flat 30% regardless of holding period; no loss set-off / carry-forward.",
        )

    # ---- Debt MF: slab rate (post-2023 acquisition) ----
    if asset_type == "debt_mf":
        return CapitalGainsResult(
            asset_type=asset_type,
            asset_subtype=asset_subtype,
            purchase_price=purchase_price,
            sale_price=sale_price,
            purchase_date=pdate.isoformat(),
            sale_date=sdate.isoformat(),
            holding_period_days=days,
            holding_period_years=years,
            classification="SLAB_RATE",
            gain_amount=gain,
            exemption_used=0.0,
            taxable_gain=max(0.0, gain),
            tax_payable=None,  # depends on caller's marginal slab
            indexation_used=False,
            applicable_rate=None,
            surcharge_cess_note=SURCHARGE_CESS_NOTE,
            note="taxed at marginal slab rate (Sec 50AA, debt MF acquired on/after 1 Apr 2023; no LTCG benefit, no indexation).",
        )

    # ---- All other asset types: STCG vs LTCG threshold split ----
    threshold_years = _THRESHOLDS_YEARS[asset_type]
    is_long_term = years > threshold_years
    classification = "LTCG" if is_long_term else "STCG"

    exemption = 0.0
    indexation_applied = False
    rate = None
    note: str | None = None

    if asset_type == "equity_listed":
        if is_long_term:
            # Sec 112A: ₹1.25L annual exemption, 12.5% on excess
            exemption = min(max(0.0, gain), EQUITY_LTCG_EXEMPTION)
            rate = EQUITY_LTCG_RATE
        else:
            # Sec 111A: 20% STCG (Budget 2024 raised from 15%)
            rate = EQUITY_STCG_RATE

    elif asset_type == "unlisted_equity":
        if is_long_term:
            rate = UNLISTED_EQUITY_LTCG_RATE
            note = "Unlisted equity LTCG taxed at 12.5% (no indexation post-Budget 2024)."
        else:
            # Unlisted STCG taxed at slab rate — return None for tax_payable
            return CapitalGainsResult(
                asset_type=asset_type,
                asset_subtype=asset_subtype,
                purchase_price=purchase_price,
                sale_price=sale_price,
                purchase_date=pdate.isoformat(),
                sale_date=sdate.isoformat(),
                holding_period_days=days,
                holding_period_years=years,
                classification="STCG",
                gain_amount=gain,
                exemption_used=0.0,
                taxable_gain=max(0.0, gain),
                tax_payable=None,
                indexation_used=False,
                applicable_rate=None,
                surcharge_cess_note=SURCHARGE_CESS_NOTE,
                note="Unlisted equity STCG taxed at marginal slab rate (Sec 111A does not apply — only listed equity).",
            )

    elif asset_type == "property":
        if is_long_term:
            if indexation:
                rate = PROPERTY_LTCG_WITH_INDEX_RATE
                indexation_applied = True
                note = (
                    "20% LTCG with indexation chosen (taxpayer option for property "
                    "acquired before 23 Jul 2024 — Finance Act 2024). Indexed cost "
                    "must be supplied externally; engine treats purchase_price as "
                    "already-indexed cost."
                )
            else:
                rate = PROPERTY_LTCG_NO_INDEX_RATE
                note = "12.5% LTCG without indexation (default post-Budget 2024)."
        else:
            # Property STCG: slab rate
            return CapitalGainsResult(
                asset_type=asset_type,
                asset_subtype=asset_subtype,
                purchase_price=purchase_price,
                sale_price=sale_price,
                purchase_date=pdate.isoformat(),
                sale_date=sdate.isoformat(),
                holding_period_days=days,
                holding_period_years=years,
                classification="STCG",
                gain_amount=gain,
                exemption_used=0.0,
                taxable_gain=max(0.0, gain),
                tax_payable=None,
                indexation_used=False,
                applicable_rate=None,
                surcharge_cess_note=SURCHARGE_CESS_NOTE,
                note="Property STCG taxed at marginal slab rate.",
            )

    elif asset_type == "gold":
        if is_long_term:
            if indexation:
                rate = GOLD_LTCG_WITH_INDEX_RATE
                indexation_applied = True
                note = "20% LTCG with indexation chosen (taxpayer option for gold acquired before 23 Jul 2024)."
            else:
                rate = GOLD_LTCG_NO_INDEX_RATE
                note = "12.5% LTCG without indexation (default post-Budget 2024)."
        else:
            # Gold STCG: slab rate
            return CapitalGainsResult(
                asset_type=asset_type,
                asset_subtype=asset_subtype,
                purchase_price=purchase_price,
                sale_price=sale_price,
                purchase_date=pdate.isoformat(),
                sale_date=sdate.isoformat(),
                holding_period_days=days,
                holding_period_years=years,
                classification="STCG",
                gain_amount=gain,
                exemption_used=0.0,
                taxable_gain=max(0.0, gain),
                tax_payable=None,
                indexation_used=False,
                applicable_rate=None,
                surcharge_cess_note=SURCHARGE_CESS_NOTE,
                note="Gold STCG taxed at marginal slab rate.",
            )

    # If we reach here, rate is set and gain may be positive or negative.
    if gain <= 0:
        # Loss — no tax. We still return a structured zero-tax result.
        return CapitalGainsResult(
            asset_type=asset_type,
            asset_subtype=asset_subtype,
            purchase_price=purchase_price,
            sale_price=sale_price,
            purchase_date=pdate.isoformat(),
            sale_date=sdate.isoformat(),
            holding_period_days=days,
            holding_period_years=years,
            classification=classification,
            gain_amount=gain,
            exemption_used=0.0,
            taxable_gain=0.0,
            tax_payable=0.0,
            indexation_used=indexation_applied,
            applicable_rate=rate,
            surcharge_cess_note=SURCHARGE_CESS_NOTE,
            note=(note or "Loss — no tax. Loss may be set off / carried forward per Sec 70-74."),
        )

    taxable_gain = max(0.0, gain - exemption)
    tax = taxable_gain * rate

    return CapitalGainsResult(
        asset_type=asset_type,
        asset_subtype=asset_subtype,
        purchase_price=purchase_price,
        sale_price=sale_price,
        purchase_date=pdate.isoformat(),
        sale_date=sdate.isoformat(),
        holding_period_days=days,
        holding_period_years=years,
        classification=classification,
        gain_amount=gain,
        exemption_used=exemption,
        taxable_gain=taxable_gain,
        tax_payable=tax,
        indexation_used=indexation_applied,
        applicable_rate=rate,
        surcharge_cess_note=SURCHARGE_CESS_NOTE,
        note=note,
    )
