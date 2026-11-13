"""REQ-F-005 — deterministic verdict composition.

The determinism test is the important one: it is what makes a changed verdict
between two runs a defect rather than a coin flip.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medcheck.adjudicator import guard
from medcheck.adjudicator.verdict import compose
from medcheck.contracts import (
    CODE_ALL_CHECKS_PASSED,
    CODE_COVERAGE_GAP,
    CODE_DDI_MAJOR,
    CODE_DOSE_CEILING,
    AdjudicationResult,
    AuthorityViolation,
    Finding,
    NormalizedDose,
    Severity,
    Verdict,
)
from medcheck.pipeline import process_case

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"


def _load(name: str) -> dict:
    return json.loads((CASES / name).read_text(encoding="utf-8"))


def _finding(code: str, rule_id: str, severity: Severity, table_version: str) -> Finding:
    return Finding(
        rule_id=rule_id,
        code=code,
        severity=severity,
        statement="synthetic finding for verdict tests",
        table_version=table_version,
    )


def test_output_is_byte_identical_over_30_runs(tables):
    """REQ-F-005: same input + same table version => byte-identical JSON, 30/30."""
    case = _load("c04_block_contraindicated.json")
    outputs = {
        json.dumps(process_case(case, tables=tables).result.to_dict(), sort_keys=True)
        for _ in range(30)
    }
    assert len(outputs) == 1


def test_verdict_precedence_order(tables):
    """[REQ-F-005] Blueprint section 5: a BLOCK condition outranks a COVERAGE_GAP HOLD."""
    findings = [
        _finding(CODE_COVERAGE_GAP, "SYS-COVERAGE-001", Severity.MAJOR, tables.version),
        _finding(CODE_DOSE_CEILING, "DOSE-001", Severity.MAJOR, tables.version),
    ]
    result = compose(
        case_id="synthetic",
        findings=findings,
        coverage_complete=False,
        normalized=[],
        table_version=tables.version,
    )
    assert result.verdict is Verdict.BLOCK


def test_major_interaction_holds_not_blocks(tables):
    """[REQ-F-005] major interaction holds not blocks."""
    findings = [_finding(CODE_DDI_MAJOR, "DDI-001", Severity.MAJOR, tables.version)]
    result = compose(
        case_id="synthetic",
        findings=findings,
        coverage_complete=True,
        normalized=[],
        table_version=tables.version,
    )
    assert result.verdict is Verdict.HOLD


def test_clean_case_approves_with_explicit_pass_finding(tables):
    """[REQ-F-005] Rule 6: APPROVE is only reachable with zero findings and full coverage."""
    result = compose(
        case_id="synthetic",
        findings=[],
        coverage_complete=True,
        normalized=[NormalizedDose("warfarin", 5.0, 10.0, "G1-G2")],
        table_version=tables.version,
    )
    assert result.verdict is Verdict.APPROVE
    assert CODE_ALL_CHECKS_PASSED in result.codes


def test_incomplete_coverage_without_findings_still_holds(tables):
    """[REQ-F-005] Defensive branch: no findings but no coverage proof must not approve."""
    result = compose(
        case_id="synthetic",
        findings=[],
        coverage_complete=False,
        normalized=[],
        table_version=tables.version,
    )
    assert result.verdict is Verdict.HOLD
    assert CODE_COVERAGE_GAP in result.codes


def test_approve_without_pass_finding_is_rejected():
    """INV-003 support: an APPROVE that skipped rule 6 cannot pass the guard."""
    forged = AdjudicationResult(
        case_id="forged",
        verdict=Verdict.APPROVE,
        findings=(),
        coverage_complete=True,
        table_version="x",
    )
    with pytest.raises(AuthorityViolation):
        guard.check_result(forged)


def test_findings_are_ordered_by_severity(tables):
    """[REQ-F-005] findings are ordered by severity."""
    findings = [
        _finding(CODE_DDI_MAJOR, "DDI-001", Severity.MAJOR, tables.version),
        _finding(CODE_COVERAGE_GAP, "SYS-COVERAGE-001", Severity.MINOR, tables.version),
    ]
    result = compose(
        case_id="synthetic",
        findings=findings,
        coverage_complete=False,
        normalized=[],
        table_version=tables.version,
    )
    assert result.findings[0].severity is Severity.MAJOR


def test_pipeline_approves_clean_case(tables):
    """[REQ-F-005] pipeline approves clean case."""
    outcome = process_case(_load("c01_approve_single.json"), tables=tables)
    assert outcome.verdict is Verdict.APPROVE, outcome.result.to_dict()


def test_pipeline_blocks_contraindicated_pair(tables):
    """[REQ-F-005] pipeline blocks contraindicated pair."""
    outcome = process_case(_load("c04_block_contraindicated.json"), tables=tables)
    assert outcome.verdict is Verdict.BLOCK
