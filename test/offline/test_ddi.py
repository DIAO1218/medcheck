"""REQ-F-003 — drug-drug interaction detection.

Fixture corpus is generated from the pinned table (scripts/build_ddi_fixtures.py)
and frozen. Honest limitation, stated so nobody over-reads a green run: positives
prove the matcher finds what the table contains, not that the table is clinically
complete (risk-list R-01).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from medcheck.adjudicator import coverage
from medcheck.contracts import CODE_DDI_CONTRAINDICATED, Medication
from medcheck.rules import ddi

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ddi_pairs.yaml"


@pytest.fixture(scope="module")
def corpus():
    return yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))


def _medications(names):
    return tuple(
        Medication(name_raw=name.title(), name_canonical=name, dose_value=1.0, dose_unit="mg", frequency_text="once daily")
        for name in names
    )


def test_positive_pairs_recall(tables, corpus):
    """REQ-F-003: all 40 table pairs are detected with the table's rule id."""
    assert len(corpus["positives"]) == 40
    missed = []
    for entry in corpus["positives"]:
        findings = ddi.check(_medications(entry["pair"]), tables)
        if not findings or findings[0].rule_id != entry["rule_id"]:
            missed.append(entry["pair"])
    assert missed == []


def test_negative_pairs_no_false_positive(tables, corpus):
    """REQ-F-003: 60 pairs absent from the table produce no interaction finding."""
    assert len(corpus["negatives"]) == 60
    false_positives = []
    for pair in corpus["negatives"]:
        if ddi.check(_medications(pair), tables):
            false_positives.append(pair)
    assert false_positives == []


def test_contraindicated_severity_maps_to_its_own_code(tables):
    """REQ-F-003 / blueprint section 5: contra comes before major."""
    findings = ddi.check(_medications(["simvastatin", "clarithromycin"]), tables)
    assert [finding.code for finding in findings] == [CODE_DDI_CONTRAINDICATED]


def test_pair_order_does_not_matter(tables):
    """[REQ-F-003] Symmetric lookup: (a,b) and (b,a) are the same pair."""
    forward = ddi.check(_medications(["warfarin", "aspirin"]), tables)
    backward = ddi.check(_medications(["aspirin", "warfarin"]), tables)
    assert [f.rule_id for f in forward] == [f.rule_id for f in backward]


def test_declared_holes_are_reported_as_gaps(tables, corpus):
    """INV-001 support: a declared hole is a COVERAGE_GAP, not a silent pass."""
    assert len(corpus["holes"]) == 2
    for entry in corpus["holes"]:
        report = coverage.assess(_medications(entry["pair"]), tables)
        assert not report.complete
        assert report.holes


def test_single_drug_has_no_pair_findings(tables):
    """[REQ-F-003] single drug has no pair findings."""
    assert ddi.check(_medications(["warfarin"]), tables) == []


def test_duplicate_drug_is_checked_once(tables):
    """[REQ-F-003] The same drug written twice is not a pair with itself."""
    duplicates = _medications(["aspirin", "aspirin"])
    assert ddi.check(duplicates, tables) == []
