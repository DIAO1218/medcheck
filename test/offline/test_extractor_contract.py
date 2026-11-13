"""REQ-F-001 — extraction contract, offline path."""

from __future__ import annotations

import dataclasses

import pytest

from medcheck.contracts import FORBIDDEN_AUTHORITY_FIELDS, ExtractionRecord
from medcheck.extractor import heuristic


def test_fixture_records_schema_valid(tables):
    """REQ-F-001: every fixture note yields a well-formed record."""
    record = heuristic.extract(
        "Warfarin 5 mg once daily. Aspirin 100 mg once daily. eGFR 55.", tables.vocabulary
    )
    assert isinstance(record, ExtractionRecord)
    assert {med.name_canonical for med in record.medications} == {"warfarin", "aspirin"}
    assert record.egfr == 55.0
    assert record.prompt_version == heuristic.VERSION


def test_contract_has_no_authority_fields():
    """INV-003 support: there is nowhere to put a verdict."""
    names = {field.name for field in dataclasses.fields(ExtractionRecord)}
    assert names.isdisjoint(FORBIDDEN_AUTHORITY_FIELDS)


def test_medication_has_no_normalized_dose():
    """[REQ-F-001] A dose in mg/day may only come from rules.units."""
    names = {field.name for field in dataclasses.fields(ExtractionRecord)}
    assert "dose_mg_per_day" not in names


def test_unparsed_fields_are_reported_not_dropped(tables):
    """[REQ-F-001] P-06: a frequency outside the grammar is surfaced, not defaulted."""
    record = heuristic.extract("Warfarin 5 mg when required.", tables.vocabulary)
    assert any("frequency" in item for item in record.unparsed)


def test_unknown_drug_is_kept_and_flagged(tables):
    """[REQ-F-001] The extractor must not decide that an unknown word is not a drug."""
    record = heuristic.extract("Morphine 10 mg once daily.", tables.vocabulary)
    assert record.medications[0].name_canonical == "morphine"
    assert any("unknown vocabulary" in item for item in record.unparsed)


def test_missing_egfr_is_none(tables):
    """[REQ-F-001] missing egfr is none."""
    record = heuristic.extract("Warfarin 5 mg once daily.", tables.vocabulary)
    assert record.egfr is None


def test_extraction_is_deterministic(tables):
    """[REQ-F-001] extraction is deterministic."""
    note = "Digoxin 125 mcg once daily. eGFR 40."
    first = heuristic.extract(note, tables.vocabulary)
    second = heuristic.extract(note, tables.vocabulary)
    assert first == second


def test_empty_note_yields_empty_record(tables):
    """[REQ-F-001] empty note yields empty record."""
    record = heuristic.extract("Patient reviewed, no prescription found.", tables.vocabulary)
    assert record.medications == ()
