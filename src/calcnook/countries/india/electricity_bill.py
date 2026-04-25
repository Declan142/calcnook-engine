"""India electricity bill calculator — generic slab-tariff engine.

Different DISCOMs (electricity distribution companies) apply different slab
structures. This module provides:
    1. A generic slab engine that works for any DISCOM.
    2. Pre-built presets for BESCOM (Karnataka), MSEB/MSEDCL (Maharashtra),
       and BSES Rajdhani/Yamuna (Delhi).

Slab format: [(upper_bound_units, rate_per_unit), ...]
    The final slab should have upper_bound = float("inf") to cover all units above.
    First slab: units 0 → upper_bound[0] at rate[0].
    Subsequent slabs: units from previous upper_bound+1 to current upper_bound.

Units are in kWh (kilowatt-hours), rates in ₹/kWh.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# DISCOM presets — approximate rates (verify with latest DISCOM tariff orders)
# ---------------------------------------------------------------------------

# BESCOM (Bangalore Electricity Supply Company) — Domestic / Residential
# Tariff Order 2023. Rates ₹/unit.
BESCOM_RESIDENTIAL: list[tuple[float, float]] = [
    (30, 0.00),        # 0-30 units: free (BPL households)
    (100, 4.10),       # 31-100 units
    (200, 5.55),       # 101-200 units
    (500, 7.10),       # 201-500 units
    (float("inf"), 7.95),  # above 500 units
]

# MSEDCL (Maharashtra State Electricity Distribution Company) — Residential
# Applicable for urban consumers. Rates ₹/unit.
MSEB_RESIDENTIAL: list[tuple[float, float]] = [
    (100, 3.78),
    (300, 9.15),
    (500, 10.60),
    (float("inf"), 11.46),
]

# BSES Delhi (Rajdhani + Yamuna) — Domestic residential
# DERC Tariff Order. Rates ₹/unit.
BSES_RESIDENTIAL: list[tuple[float, float]] = [
    (200, 3.00),
    (400, 4.50),
    (800, 6.50),
    (float("inf"), 7.50),
]


@dataclass(frozen=True)
class SlabDetail:
    """Single slab contribution to the bill."""
    slab_upper: float
    rate_per_unit: float
    units_in_slab: float
    energy_charge: float

    def to_dict(self) -> dict:
        return {
            "slab_upper": self.slab_upper if self.slab_upper != float("inf") else None,
            "rate_per_unit": self.rate_per_unit,
            "units_in_slab": round(self.units_in_slab, 3),
            "energy_charge": round(self.energy_charge, 2),
        }


@dataclass(frozen=True)
class ElectricityBillResult:
    """Result of an electricity bill calculation."""
    units_consumed: float
    energy_charge: float
    fixed_charges: float
    fuel_surcharge: float
    electricity_duty: float
    total_bill: float
    slab_breakdown: tuple

    def to_dict(self) -> dict:
        return {
            "units_consumed": self.units_consumed,
            "energy_charge": round(self.energy_charge, 2),
            "fixed_charges": round(self.fixed_charges, 2),
            "fuel_surcharge": round(self.fuel_surcharge, 2),
            "electricity_duty": round(self.electricity_duty, 2),
            "total_bill": round(self.total_bill, 2),
            "slab_breakdown": [s.to_dict() for s in self.slab_breakdown],
        }


def calculate(
    units_consumed: float,
    slabs: list[tuple[float, float]],
    fixed_charges: float = 0.0,
    fuel_surcharge_per_unit: float = 0.0,
    electricity_duty_percent: float = 0.0,
) -> ElectricityBillResult:
    """Compute an electricity bill using progressive slab tariffs.

    The energy charge is computed progressively — each slab's rate applies
    only to the units consumed within that slab's range.

    Total bill = energy_charge + fixed_charges + fuel_surcharge + electricity_duty
    where:
        fuel_surcharge = units_consumed * fuel_surcharge_per_unit
        electricity_duty = (energy_charge + fuel_surcharge) * electricity_duty_percent / 100

    Args:
        units_consumed: Total electricity consumption in kWh.
        slabs: List of (upper_bound_units, rate_per_unit) tuples. The upper bound
            of the final slab should be float("inf") to cover all remaining units.
            Example: [(100, 4.10), (300, 5.55), (float("inf"), 7.10)]
        fixed_charges: Monthly fixed / demand charges in ₹ (customer charge,
            meter rent, etc.).
        fuel_surcharge_per_unit: Fuel adjustment charge / power purchase cost
            surcharge per unit in ₹/kWh.
        electricity_duty_percent: State electricity duty as a percentage of
            energy charges + fuel surcharge (e.g. 5.0 for 5%).

    Returns:
        ElectricityBillResult.

    Raises:
        ValueError: if inputs are invalid.

    Example (BESCOM):
        >>> r = calculate(150, BESCOM_RESIDENTIAL, fixed_charges=50)
        >>> r.energy_charge  # 30 free + 70 @ 4.10 + 50 @ 5.55
        564.5
    """
    if units_consumed < 0:
        raise ValueError("units_consumed must be >= 0")
    if not slabs:
        raise ValueError("slabs must not be empty")
    if fixed_charges < 0:
        raise ValueError("fixed_charges must be >= 0")
    if fuel_surcharge_per_unit < 0:
        raise ValueError("fuel_surcharge_per_unit must be >= 0")
    if electricity_duty_percent < 0:
        raise ValueError("electricity_duty_percent must be >= 0")

    breakdown: List[SlabDetail] = []
    energy_charge = 0.0
    prev_upper = 0.0

    for upper, rate in slabs:
        if units_consumed <= prev_upper:
            break
        chunk = min(units_consumed, upper) - prev_upper
        if chunk <= 0:
            prev_upper = upper
            continue
        cost = chunk * rate
        energy_charge += cost
        breakdown.append(SlabDetail(
            slab_upper=upper,
            rate_per_unit=rate,
            units_in_slab=chunk,
            energy_charge=cost,
        ))
        prev_upper = upper

    fuel = units_consumed * fuel_surcharge_per_unit
    duty = (energy_charge + fuel) * electricity_duty_percent / 100.0
    total = energy_charge + fixed_charges + fuel + duty

    return ElectricityBillResult(
        units_consumed=units_consumed,
        energy_charge=energy_charge,
        fixed_charges=fixed_charges,
        fuel_surcharge=fuel,
        electricity_duty=duty,
        total_bill=total,
        slab_breakdown=tuple(breakdown),
    )
