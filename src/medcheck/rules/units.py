"""Unit normalisation. Deterministic, table-driven, no inference.

`to_mg_per_day` is the only place a dose becomes a number. If it cannot compute
one, it raises; it never returns a plausible default (that would be an
authority field invented by omission, INV-003).
"""

from __future__ import annotations

import math

from ..contracts import Medication, UnconvertibleUnit, UnsupportedFrequency
from .loader import RuleTables


def to_mg(dose_value: float, dose_unit: str, tables: RuleTables) -> float:
    """REQ-F-002 / INV-002: normalize finite doses without guessing invalid values."""
    unit = dose_unit.strip().lower()
    if unit not in tables.conversions:
        raise UnconvertibleUnit(f"unit '{dose_unit}' has no entry in the conversion table")
    if not math.isfinite(dose_value):
        raise UnconvertibleUnit("dose value must be finite")
    if dose_value < 0:
        raise ValueError("dose value must not be negative")
    converted = dose_value * tables.conversions[unit]
    if not math.isfinite(converted):
        raise UnconvertibleUnit("converted dose must be finite")
    return converted


def parse_frequency(frequency_text: str | None, tables: RuleTables) -> float:
    """Return doses per day. Narrow grammar by design (P-06)."""
    if not frequency_text:
        raise UnsupportedFrequency("frequency is missing")
    key = frequency_text.strip().lower()
    if key not in tables.frequencies:
        raise UnsupportedFrequency(f"frequency '{frequency_text}' is outside the supported grammar")
    return tables.frequencies[key]


def to_mg_per_day(medication: Medication, tables: RuleTables) -> float:
    """REQ-F-002 / INV-002: reject overflow before a daily dose reaches adjudication."""
    if medication.dose_value is None:
        raise UnconvertibleUnit(f"{medication.name_raw}: no dose value")
    if not medication.dose_unit:
        raise UnconvertibleUnit(f"{medication.name_raw}: no dose unit")
    per_dose = to_mg(medication.dose_value, medication.dose_unit, tables)
    per_day = parse_frequency(medication.frequency_text, tables)
    daily = per_dose * per_day
    if not math.isfinite(daily):
        raise UnconvertibleUnit("daily dose must be finite")
    return daily


def mg(value: float) -> str:
    """Stable formatting for findings and audit: no float noise in prose."""
    if value == int(value):
        return f"{int(value)} mg"
    return f"{value:.3f}".rstrip("0").rstrip(".") + " mg"
