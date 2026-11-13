"""REQ-F-006 and REQ-Q-002 — advisory conformance and length."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medcheck.contracts import Finding, Severity, Verdict
from medcheck.pipeline import process_case
from medcheck.renderer import template

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"


def _case(name: str) -> dict:
    return json.loads((CASES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture",
    ["c01_approve_single.json", "c04_block_contraindicated.json", "c14_hold_unknown_drug.json", "c05_block_ceiling.json"],
)
def test_statements_map_to_findings_or_templates(fixture, tables):
    """REQ-F-006: every line of the advisory is a finding or a fixed template."""
    outcome = process_case(_case(fixture), tables=tables)
    violations = template.conformance_violations(outcome.result, outcome.advisory)
    assert violations == [], violations


def test_renderer_introduces_no_new_numbers(tables):
    """REQ-F-006: a number in prose that is in no finding is a defect."""
    outcome = process_case(_case("c05_block_ceiling.json"), tables=tables)
    tampered = outcome.advisory + "\n[moderate] consider 999 mg instead."
    violations = template.conformance_violations(outcome.result, tampered)
    assert any("999" in violation for violation in violations)


def test_renderer_cannot_soften_the_verdict(tables):
    """[REQ-F-006] A BLOCK advisory whose header says APPROVE is caught by conformance."""
    outcome = process_case(_case("c04_block_contraindicated.json"), tables=tables)
    tampered = outcome.advisory.replace("BLOCK", "APPROVE")
    violations = template.conformance_violations(outcome.result, tampered)
    assert any("header" in violation for violation in violations)


def test_advisory_word_cap(tables):
    """REQ-Q-002: a result with many findings still renders <= 200 words."""
    outcome = process_case(_case("c14_hold_unknown_drug.json"), tables=tables)
    many = tuple(
        Finding("SYS-FIELD-001", "FIELD_UNPARSED", Severity.MODERATE, f"field {index} left unparsed", tables.version)
        for index in range(60)
    )
    from dataclasses import replace

    bloated = replace(outcome.result, findings=many)
    text = template.render(bloated)
    assert len(text.split()) <= template.MAX_WORDS


def test_header_states_not_for_clinical_use(tables):
    """[REQ-F-006] Every advisory carries the non-clinical disclaimer, in every verdict."""
    for fixture in ("c01_approve_single.json", "c04_block_contraindicated.json", "c14_hold_unknown_drug.json"):
        outcome = process_case(_case(fixture), tables=tables)
        assert "NOT FOR CLINICAL USE" in outcome.advisory


def test_verdict_prefixes():
    """[REQ-F-006] The three verdicts map to three unmistakable headers."""
    from medcheck.contracts import AdjudicationResult

    for verdict, prefix in (
        (Verdict.APPROVE, "APPROVE"),
        (Verdict.HOLD, "HOLD FOR REVIEW"),
        (Verdict.BLOCK, "BLOCK"),
    ):
        result = AdjudicationResult("x", verdict, (), True, "v")
        assert template.header(result).startswith(prefix)
