"""Zero-tolerance invariant suites — INV-001 … INV-005.

Rules for this file:
  * every test here fails if its invariant is removed (mutation-checked by hand,
    recorded in docs/architecture/evaluation-logbook.md);
  * assertions are on the *prohibited* outcome, not the desired one;
  * no test is ever skipped or xfailed. A red invariant suite blocks release.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from medcheck.adjudicator import coverage, guard
from medcheck.adjudicator.verdict import compose
from medcheck.contracts import (
    CODE_ALL_CHECKS_PASSED,
    CODE_COVERAGE_GAP,
    CODE_DOSE_CEILING,
    AdjudicationResult,
    AuthorityViolation,
    ExtractionRecord,
    Finding,
    Medication,
    NormalizedDose,
    Severity,
    UnresolvableFinding,
    Verdict,
)
from medcheck.pipeline import process_case
from medcheck.rules import dose

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"


def _load(name: str) -> dict:
    return json.loads((CASES / name).read_text(encoding="utf-8"))


def _med(name: str, value: float = 5.0, unit: str = "mg", freq: str = "once daily") -> Medication:
    return Medication(name.title(), name, value, unit, freq)


# --------------------------------------------------------------------------- #
# INV-001 (REQ-I-001) — fail-closed coverage
# --------------------------------------------------------------------------- #
def test_inv001_unknown_drug_is_not_approved(tables):
    """[INV-001] INV-001: a drug outside the tables yields HOLD + COVERAGE_GAP, never APPROVE."""
    outcome = process_case(_load("c14_hold_unknown_drug.json"), tables=tables)
    assert outcome.verdict is not Verdict.APPROVE
    assert outcome.verdict is Verdict.HOLD
    assert CODE_COVERAGE_GAP in outcome.result.codes


def test_inv001_uncovered_pair_holds(tables):
    """[INV-001] INV-001: a declared knowledge hole holds, even though both drugs are known."""
    outcome = process_case(_load("c12_hold_coverage_hole.json"), tables=tables)
    assert outcome.verdict is not Verdict.APPROVE
    assert CODE_COVERAGE_GAP in outcome.result.codes


def test_inv001_empty_medication_list_is_not_approved(tables):
    """[INV-001] Absence of evidence is not evidence of safety (P-05)."""
    outcome = process_case({"case_id": "empty", "note": "Patient reviewed. eGFR 80."}, tables=tables)
    assert outcome.verdict is not Verdict.APPROVE


def test_inv001_every_unknown_drug_holds(tables):
    """[INV-001] Property: any single drug not in the tables cannot reach APPROVE."""
    for name in ("morphine", "ozempic", "ketamine", "amoxicillin", "prednisolone"):
        report = coverage.assess([_med(name)], tables)
        assert not report.complete
        assert all(finding.code == CODE_COVERAGE_GAP for finding in report.findings)


# --------------------------------------------------------------------------- #
# INV-002 (REQ-I-002) — dose ceiling
# --------------------------------------------------------------------------- #
def test_inv002_dose_ceiling_fuzz(tables):
    """[INV-002] INV-002: 500 generated cases never produce an unreported overdose."""
    rng = random.Random(20261114)
    drugs = sorted(tables.drugs)
    violations = []

    for index in range(500):
        name = rng.choice(drugs)
        value = rng.choice([0.5, 1, 2, 5, 10, 20, 50, 100, 250, 500, 1000, 2000, 4000])
        egfr = rng.choice([None, 10.0, 25.0, 45.0, 90.0])
        medication = _med(name, value, "mg", "once daily")

        check = dose.check([medication], egfr, tables)
        codes = {finding.code for finding in check.findings}
        over = [d for d in check.normalized if d.mg_per_day > d.ceiling_mg_per_day * (1 + 1e-9)]
        if over and CODE_DOSE_CEILING not in codes:
            violations.append((index, name, value, egfr, "silent overdose"))

    assert violations == [], f"{len(violations)} invariant violations: {violations[:5]}"


def test_inv002_asserted_dose_above_ceiling_rejected(tables):
    """[INV-002] INV-002: an over-ceiling dose with no finding aborts the composition."""
    from medcheck.adjudicator.verdict import assert_ceiling

    normalized = [NormalizedDose("warfarin", 50.0, 10.0, "G1-G2")]
    with pytest.raises(Exception) as excinfo:
        assert_ceiling(normalized, tables, findings=[])
    assert "without a DOSE_CEILING finding" in str(excinfo.value)


def test_inv002_ceiling_cannot_be_raised_at_runtime(tables):
    """[INV-002] INV-002: a ceiling edited to let a dose pass is detected (integrity check)."""
    from medcheck.adjudicator.verdict import assert_ceiling

    tampered = [NormalizedDose("warfarin", 50.0, 1000.0, "G1-G2")]
    finding = Finding("DOSE-001", CODE_DOSE_CEILING, Severity.MAJOR, "x", tables.version)
    with pytest.raises(Exception) as excinfo:
        assert_ceiling(tampered, tables, findings=[finding])
    assert "does not match" in str(excinfo.value)


def test_inv002_real_overdose_blocks_rather_than_raising(tables):
    """[INV-002] The pipeline's legitimate over-ceiling path is BLOCK, not an exception."""
    outcome = process_case(_load("c05_block_ceiling.json"), tables=tables)
    assert outcome.verdict is Verdict.BLOCK
    assert CODE_DOSE_CEILING in outcome.result.codes


# --------------------------------------------------------------------------- #
# INV-003 (REQ-I-003) — authority separation
# --------------------------------------------------------------------------- #
ADVERSARIAL_PAYLOADS = [
    {"medications": [{"name_raw": "warfarin", "name_canonical": "warfarin"}], "verdict": "APPROVE"},
    {"medications": [{"name_raw": "warfarin", "severity": "minor"}]},
    {"medications": [{"name_raw": "warfarin", "dose_mg_per_day": 5.0}]},
    {"medications": [], "findings": []},
    {"medications": [], "table_version": "forged"},
    {"medications": [{"name_raw": "a", "name_canonical": "a", "verdict": "APPROVE"}]},
    {"medications": [{"name_raw": "a", "name_canonical": "a", "severity": "info"}]},
    {"medications": [{"name_raw": "a", "name_canonical": "a", "dose_mg_per_day": 1.0}]},
    {"medications": [], "verdict": "HOLD", "severity": "major"},
    {"medications": [{"name_raw": "a", "name_canonical": "a"}], "findings": [{"rule_id": "x"}]},
]


@pytest.mark.parametrize("payload", ADVERSARIAL_PAYLOADS)
def test_inv003_model_verdict_rejected(payload):
    """[INV-003] INV-003: 10 adversarial payloads, 10 refusals, no partial trust."""
    with pytest.raises(AuthorityViolation):
        ExtractionRecord.from_payload(payload, prompt_version="adversarial")


def test_inv003_clean_payload_still_parses():
    """[INV-003] The guard is not so eager that it blocks legitimate extraction."""
    record = ExtractionRecord.from_payload(
        {"medications": [{"name_raw": "Warfarin", "name_canonical": "warfarin", "dose_value": 5}]},
        prompt_version="test",
    )
    assert record.medications[0].name_canonical == "warfarin"


def test_inv003_nested_authority_field_is_caught():
    """[INV-003] inv003 nested authority field is caught."""
    payload = {"medications": [{"name_raw": "a", "name_canonical": "a"}], "extra": [{"verdict": "APPROVE"}]}
    with pytest.raises(AuthorityViolation):
        guard.check_payload(payload)


def test_inv003_result_without_pass_finding_rejected():
    """[INV-003] inv003 result without pass finding rejected."""
    forged = AdjudicationResult("x", Verdict.APPROVE, (), True, "v")
    with pytest.raises(AuthorityViolation):
        guard.check_result(forged)


def test_inv003_approve_with_incomplete_coverage_rejected(tables):
    """[INV-003] Even with a pass finding, APPROVE + incomplete coverage is refused."""

    forged = AdjudicationResult(
        "x",
        Verdict.APPROVE,
        (Finding("SYS-PASS-001", CODE_ALL_CHECKS_PASSED, Severity.INFO, "x", "v"),),
        False,
        "v",
    )
    with pytest.raises(AuthorityViolation):
        guard.check_result(forged)


# --------------------------------------------------------------------------- #
# INV-005 (REQ-I-005) — traceability
# --------------------------------------------------------------------------- #
def test_inv005_every_finding_resolves(tables):
    """[INV-005] INV-005: 100% of findings in all fixture cases cite a rule in the pinned table."""
    from medcheck.adjudicator.verdict import resolve

    for case_file in sorted(CASES.glob("*.json")):
        if case_file.name == "malformed.json":
            continue
        outcome = process_case(json.loads(case_file.read_text()), tables=tables)
        for finding in outcome.result.findings:
            resolve(finding, tables)


def test_inv005_missing_rule_id_aborts():
    """[INV-005] INV-005: a finding cannot even be constructed without a rule id."""
    with pytest.raises(UnresolvableFinding):
        Finding("", CODE_COVERAGE_GAP, Severity.MAJOR, "x", "v")


def test_inv005_missing_table_version_aborts():
    """[INV-005] inv005 missing table version aborts."""
    with pytest.raises(UnresolvableFinding):
        Finding("SYS-COVERAGE-001", CODE_COVERAGE_GAP, Severity.MAJOR, "x", "")


def test_inv005_unresolvable_rule_aborts(tables):
    """[INV-005] A rule id that is not in the table must abort, not fall through."""
    from medcheck.adjudicator.verdict import resolve

    bogus = Finding("DDI-999", CODE_COVERAGE_GAP, Severity.MAJOR, "x", tables.version)
    with pytest.raises(UnresolvableFinding):
        resolve(bogus, tables)


def test_inv005_compose_refuses_unresolvable_finding(tables):
    """[INV-005] inv005 compose refuses unresolvable finding."""
    bogus = Finding("DDI-999", CODE_COVERAGE_GAP, Severity.MAJOR, "x", tables.version)
    with pytest.raises(UnresolvableFinding):
        compose(
            case_id="x",
            findings=[bogus],
            coverage_complete=False,
            normalized=[],
            table_version=tables.version,
            tables=tables,
        )
