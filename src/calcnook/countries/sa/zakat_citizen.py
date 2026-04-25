"""Saudi citizen / GCC national Zakat estimator (ZATCA-collected).

IMPORTANT — SIMPLIFIED ESTIMATOR ONLY:
    This module computes 2.5% of the caller-supplied zakat_base. It is a
    simplified estimator. Real ZATCA zakat computation is significantly more
    complex: the zakat base equals adjusted equity + long-term liabilities
    minus fixed assets minus deferred costs minus certain investments, all per
    ZATCA regulations and GAAP-to-Zakat adjustments. Taxpayers must submit the
    official ZATCA Zakat Return. Consult ZATCA (zatca.gov.sa) for actual filing.

Reference: ZATCA Zakat Regulations (General Authority of Zakat and Tax, KSA).
"""

from __future__ import annotations

from dataclasses import dataclass

ZAKAT_RATE = 0.025  # 2.5% — Zakat al-Mal rate universally applied


@dataclass(frozen=True)
class SAZakatCitizenResult:
    """Result of a Saudi citizen Zakat estimation."""
    zakat_base: float
    zakat_due: float
    rate: float
    disclaimer: str

    def to_dict(self) -> dict:
        return {
            "zakat_base": round(self.zakat_base, 2),
            "zakat_due": round(self.zakat_due, 2),
            "rate": self.rate,
            "disclaimer": self.disclaimer,
        }


_DISCLAIMER = (
    "SIMPLIFIED ESTIMATOR: 2.5% of supplied zakat_base. "
    "Real ZATCA zakat base = adjusted equity + long-term liabilities "
    "- fixed assets - deferred costs - certain investments. "
    "Consult ZATCA (zatca.gov.sa) for official filing."
)


def calculate(zakat_base: float) -> SAZakatCitizenResult:
    """Estimate ZATCA-collected Zakat for Saudi / GCC nationals.

    This is a simplified 2.5% calculation on the supplied ``zakat_base``.
    The actual ZATCA zakat base differs significantly from book equity and
    requires full financial statements. Use this for quick estimates only.

    Args:
        zakat_base: Caller-computed zakat-eligible base amount in SAR.

    Returns:
        SAZakatCitizenResult.

    Raises:
        ValueError: if zakat_base is negative.

    Example:
        >>> r = calculate(1_000_000)
        >>> r.zakat_due
        25000.0
    """
    if zakat_base < 0:
        raise ValueError("zakat_base must be >= 0")

    zakat_due = zakat_base * ZAKAT_RATE

    return SAZakatCitizenResult(
        zakat_base=zakat_base,
        zakat_due=zakat_due,
        rate=ZAKAT_RATE,
        disclaimer=_DISCLAIMER,
    )
