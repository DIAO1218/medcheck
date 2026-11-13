"""REQ-F-007 — append-only, hash-chained audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medcheck.audit.log import AuditLog, hash_input
from medcheck.contracts import AuditImmutableError, AuditTamperError, MedCheckError
from medcheck.pipeline import process_case

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"


def _case(name: str) -> dict:
    return json.loads((CASES / name).read_text(encoding="utf-8"))


def _append(log: AuditLog, case_id: str) -> None:
    log.append(
        case_id=case_id,
        input_hash=hash_input("masked note"),
        table_version="v1",
        prompt_version="heuristic-v1",
        verdict="HOLD",
        findings=("COVERAGE_GAP",),
    )


def test_record_count_matches_adjudications(tmp_path, tables):
    """REQ-F-007: one audit record per adjudicated case, no more, no fewer."""
    log = AuditLog(tmp_path / "audit.jsonl")
    for name in ("c01_approve_single.json", "c04_block_contraindicated.json", "c14_hold_unknown_drug.json"):
        process_case(_case(name), tables=tables, audit=log)
    assert len(log.records()) == 3
    assert log.verify() is True


def test_tamper_raises_immutable_error(tmp_path):
    """REQ-F-007 / INV: 10 tamper attempts, 10 refusals."""
    log = AuditLog(tmp_path / "audit.jsonl")
    _append(log, "case-1")
    for _ in range(5):
        with pytest.raises(AuditImmutableError):
            log.update_record(case_id="case-1", verdict="APPROVE")
        with pytest.raises(AuditImmutableError):
            log.delete_record(case_id="case-1")


def test_file_edit_breaks_the_chain(tmp_path):
    """REQ-F-007: editing the JSONL out-of-band is detected, not absorbed."""
    log = AuditLog(tmp_path / "audit.jsonl")
    _append(log, "case-1")
    _append(log, "case-2")

    lines = log.path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    record["verdict"] = "APPROVE"
    lines[0] = json.dumps(record)
    log.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(AuditTamperError):
        log.verify()


def test_duplicate_case_is_rejected(tmp_path):
    """[REQ-F-007] P-18: two adjudications for one case id would fork the audit trail."""
    log = AuditLog(tmp_path / "audit.jsonl")
    _append(log, "case-1")
    with pytest.raises(MedCheckError) as excinfo:
        _append(log, "case-1")
    assert "DUPLICATE_CASE" in str(excinfo.value)


def test_audit_stores_no_case_text(tmp_path, tables):
    """INV-004: the record carries a hash, never the note."""
    log = AuditLog(tmp_path / "audit.jsonl")
    process_case(_case("c01_approve_single.json"), tables=tables, audit=log)
    raw = log.path.read_text(encoding="utf-8")
    assert "Warfarin" not in raw
    assert "eGFR" not in raw
    assert len(json.loads(raw.splitlines()[0])["input_hash"]) == 64
