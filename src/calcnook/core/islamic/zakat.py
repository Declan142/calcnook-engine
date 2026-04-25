"""Zakat al-Mal — annual 2.5% wealth obligation in Islamic finance.

Cross-cutting module: applies to any Muslim, any country. Currency-agnostic.

Nisab thresholds (the minimum wealth before zakat is due) are based on the
market price of gold (85 grams) or silver (595 grams). The lower threshold
between the two is conventionally used so more people qualify. We expose
both so the caller (or a UI) can choose the policy.
"""

from __future__ import annotations

from dataclasses import dataclass


GOLD_NISAB_GRAMS = 85.0
SILVER_NISAB_GRAMS = 595.0
ZAKAT_RATE = 0.025  # 2.5%


@dataclass(frozen=True)
class ZakatResult:
    total_zakatable_assets: float
    nisab_threshold_used: float
    nisab_basis: str  # "gold" or "silver"
    is_above_nisab: bool
    zakat_due: float
    currency: str

    def to_dict(self) -> dict:
        return {
            "total_zakatable_assets": round(self.total_zakatable_assets, 2),
            "nisab_threshold_used": round(self.nisab_threshold_used, 2),
            "nisab_basis": self.nisab_basis,
            "is_above_nisab": self.is_above_nisab,
            "zakat_due": round(self.zakat_due, 2),
            "currency": self.currency,
        }


def calculate(
    cash: float = 0.0,
    gold_grams: float = 0.0,
    silver_grams: float = 0.0,
    stocks_value: float = 0.0,
    business_assets: float = 0.0,
    other_zakatable_assets: float = 0.0,
    debts: float = 0.0,
    gold_price_per_gram: float = 75.0,
    silver_price_per_gram: float = 0.90,
    nisab_basis: str = "silver",
    currency: str = "USD",
) -> ZakatResult:
    """Compute Zakat due on annual wealth.

    Zakatable assets are summed and reduced by debts. If net wealth meets the
    nisab threshold (gold or silver basis), 2.5% is owed.

    Args:
        cash: cash on hand + bank balances + savings.
        gold_grams: weight of gold owned. Personal jewelry rules vary by school;
            this calc treats all gold as zakatable. Caller should adjust.
        silver_grams: weight of silver owned.
        stocks_value: current market value of zakatable equity holdings.
            Investment shares (held for trading) are fully zakatable.
        business_assets: business inventory + receivables held for resale.
        other_zakatable_assets: any other qualifying assets (rental income held,
            agricultural produce, livestock value, etc).
        debts: outstanding debts owed by the holder, deductible from wealth.
        gold_price_per_gram: market price of gold in `currency` per gram.
            Default ~$75 USD/g (April 2026 ballpark). Pass live FX-aware figure.
        silver_price_per_gram: market price of silver in `currency` per gram.
            Default ~$0.90 USD/g (April 2026 ballpark).
        nisab_basis: "silver" (lower, more inclusive — conventional) or "gold".
        currency: ISO-4217 code for display.

    Returns:
        ZakatResult.

    Raises:
        ValueError: if inputs are invalid.

    Example:
        >>> r = calculate(cash=10_000, stocks_value=15_000, debts=2_000,
        ...               currency="USD", gold_price_per_gram=75,
        ...               silver_price_per_gram=0.90, nisab_basis="silver")
        >>> r.is_above_nisab, round(r.zakat_due, 2)
        (True, 575.0)
    """
    for name, val in [
        ("cash", cash),
        ("gold_grams", gold_grams),
        ("silver_grams", silver_grams),
        ("stocks_value", stocks_value),
        ("business_assets", business_assets),
        ("other_zakatable_assets", other_zakatable_assets),
        ("debts", debts),
        ("gold_price_per_gram", gold_price_per_gram),
        ("silver_price_per_gram", silver_price_per_gram),
    ]:
        if val < 0:
            raise ValueError(f"{name} must be >= 0")
    if nisab_basis not in {"gold", "silver"}:
        raise ValueError("nisab_basis must be 'gold' or 'silver'")

    gold_value = gold_grams * gold_price_per_gram
    silver_value = silver_grams * silver_price_per_gram

    total_assets = (
        cash + gold_value + silver_value + stocks_value
        + business_assets + other_zakatable_assets
    )
    net_wealth = total_assets - debts

    if nisab_basis == "gold":
        threshold = GOLD_NISAB_GRAMS * gold_price_per_gram
    else:
        threshold = SILVER_NISAB_GRAMS * silver_price_per_gram

    is_above = net_wealth >= threshold
    zakat_due = net_wealth * ZAKAT_RATE if is_above else 0.0

    return ZakatResult(
        total_zakatable_assets=net_wealth,
        nisab_threshold_used=threshold,
        nisab_basis=nisab_basis,
        is_above_nisab=is_above,
        zakat_due=max(0.0, zakat_due),
        currency=currency,
    )
