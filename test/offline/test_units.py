"""REQ-F-002 — unit normalisation.

Every case here is a fixture from the closed conversion table; a unit that is not
in the table must raise, never fall back to "assume mg".
"""

from __future__ import annotations

import pytest

from medcheck.contracts import Medication, UnconvertibleUnit, UnsupportedFrequency
from medcheck.rules.units import parse_frequency, to_mg, to_mg_per_day


def test_mcg_to_mg_conversion(tables):
    """REQ-F-002: 250 mcg once daily is 0.25 mg/day."""
    medication = Medication("Digoxin", "digoxin", 250.0, "mcg", "once daily")
    assert to_mg_per_day(medication, tables) == pytest.approx(0.25)


def test_grams_to_mg(tables):
    """REQ-F-002: 1 g = 1000 mg, and the frequency multiplies."""
    medication = Medication("Vancomycin", "vancomycin", 1.0, "g", "twice daily")
    assert to_mg_per_day(medication, tables) == pytest.approx(2000.0)


@pytest.mark.parametrize("unit", ["tab", "puff", "vial", "drop", ""])
def test_unconvertible_unit_raises(tables, unit):
    """REQ-F-002 / P-11: an unknown unit is an error, not a guess."""
    with pytest.raises(UnconvertibleUnit):
        to_mg(1.0, unit, tables)


@pytest.mark.parametrize(
    "phrase,expected",
    [("once daily", 1.0), ("bd", 2.0), ("three times daily", 3.0), ("qds", 4.0), ("q8h", 3.0)],
)
def test_frequency_grammar(tables, phrase, expected):
    """REQ-F-002: supported frequency phrases map to a doses-per-day count."""
    assert parse_frequency(phrase, tables) == expected


@pytest.mark.parametrize("phrase", ["occasionally", "as needed sometimes", "", None])
def test_unsupported_frequency_raises(tables, phrase):
    """[REQ-F-002] P-06: outside the grammar is FIELD_UNPARSED, not a default of 1."""
    with pytest.raises(UnsupportedFrequency):
        parse_frequency(phrase, tables)


def test_missing_dose_value_raises(tables):
    """REQ-F-002: no dose is not dose zero."""
    medication = Medication("Warfarin", "warfarin", None, "mg", "once daily")
    with pytest.raises(UnconvertibleUnit):
        to_mg_per_day(medication, tables)


def test_negative_dose_rejected(tables):
    """[REQ-F-002] A negative dose is nonsense; refuse rather than compute."""
    with pytest.raises(ValueError):
        to_mg(-5.0, "mg", tables)
