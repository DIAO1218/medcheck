"""The frozen evaluation set, pinned verdict by verdict (25 cases).

This is the regression backbone: each case exists because it exercises one
distinguishable outcome class, and the expected verdict is recorded here rather
than inferred from a golden file. If a change moves any of these, the diff is the
conversation.

`scripts/eval_replay.py` scores the same set; this file fixes what "correct"
means for it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medcheck.pipeline import process_case

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"

# case file -> (expected verdict, codes that must be present)
EXPECTED: dict[str, tuple[str, set[str]]] = {
    "c01_approve_single.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c02_approve_no_egfr_nonrenal.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c03_approve_at_ceiling.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c04_block_contraindicated.json": ("BLOCK", {"DDI_CONTRAINDICATED"}),
    "c05_block_ceiling.json": ("BLOCK", {"DOSE_CEILING"}),
    "c06_hold_major_ddi.json": ("HOLD", {"DDI_MAJOR"}),
    "c07_hold_minor_ddi.json": ("HOLD", {"DDI_MINOR_MODERATE"}),
    "c08_hold_moderate_ddi.json": ("HOLD", {"DDI_MINOR_MODERATE"}),
    "c09_block_renal_band.json": ("BLOCK", {"DOSE_CEILING"}),
    "c10_approve_renal_compliant.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c11_hold_missing_egfr_renal.json": ("HOLD", {"RENAL_DATA_MISSING"}),
    "c12_hold_coverage_hole.json": ("HOLD", {"COVERAGE_GAP"}),
    "c13_hold_hole_vancomycin.json": ("HOLD", {"COVERAGE_GAP"}),
    "c14_hold_unknown_drug.json": ("HOLD", {"COVERAGE_GAP"}),
    "c15_hold_two_unknown.json": ("HOLD", {"COVERAGE_GAP"}),
    "c16_hold_unparsed_frequency.json": ("HOLD", {"UNIT_UNSUPPORTED"}),
    "c17_approve_injection_ignored.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c18_hold_no_medications.json": ("HOLD", {"NO_MEDICATIONS_FOUND"}),
    "c19_block_multi.json": ("BLOCK", {"DDI_CONTRAINDICATED", "DDI_MAJOR"}),
    "c20_hold_digoxin_amiodarone.json": ("HOLD", {"DDI_MAJOR"}),
    "c21_block_gentamicin_g5.json": ("BLOCK", {"DOSE_CEILING"}),
    "c22_hold_lithium_ibuprofen.json": ("HOLD", {"DDI_MAJOR"}),
    "c23_approve_triple.json": ("APPROVE", {"ALL_CHECKS_PASSED"}),
    "c24_hold_two_renal_missing.json": ("HOLD", {"RENAL_DATA_MISSING"}),
    "c25_hold_qt_pair.json": ("HOLD", {"DDI_MAJOR"}),
}


def test_the_evaluation_set_has_25_cases():
    """DEBT-02: the frozen set is 25 cases, not the original 6.

    Deliberately contains no PHI: a committed fixture may not carry an identifier,
    even a fake one (REQ-S-001, BUG-0007). The PHI path is tested in-process in
    test_privacy.py, where the note exists only in memory.
    """
    present = {path.name for path in CASES.glob("c*.json")}
    assert present == set(EXPECTED)
    assert len(EXPECTED) == 25


@pytest.mark.parametrize("filename", sorted(EXPECTED))
def test_fixture_verdict_and_codes(filename, tables):
    """REQ-F-005 / gate 4: every case lands on its pinned verdict and codes."""
    expected_verdict, expected_codes = EXPECTED[filename]
    case = json.loads((CASES / filename).read_text(encoding="utf-8"))
    outcome = process_case(case, tables=tables)

    assert outcome.verdict.value == expected_verdict, outcome.result.to_dict()
    assert expected_codes <= set(outcome.result.codes), outcome.result.codes


def test_verdict_distribution_is_not_degenerate(tables):
    """[REQ-F-005] A suite that only ever holds would pass while proving nothing."""
    counts = {"APPROVE": 0, "HOLD": 0, "BLOCK": 0}
    for filename in EXPECTED:
        case = json.loads((CASES / filename).read_text(encoding="utf-8"))
        counts[process_case(case, tables=tables).verdict.value] += 1

    assert counts["APPROVE"] >= 5
    assert counts["HOLD"] >= 8
    assert counts["BLOCK"] >= 4
    assert sum(counts.values()) == 25


def test_injection_case_does_not_change_the_verdict(tables):
    """[REQ-F-005] The embedded instruction is data: the verdict is the one the drugs earn."""
    clean = json.loads((CASES / "c01_approve_single.json").read_text(encoding="utf-8"))
    injected = json.loads((CASES / "c17_approve_injection_ignored.json").read_text(encoding="utf-8"))

    clean_result = process_case(clean, tables=tables).result
    injected_result = process_case(injected, tables=tables).result

    assert injected_result.verdict is clean_result.verdict
    assert injected_result.codes == clean_result.codes
