"""REQ-F-008 — CLI contract and exit codes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "test" / "fixtures" / "cases"


def _run(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "medcheck.api.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )


def test_cli_emits_contract_document():
    """REQ-F-008: exit 0 and a document with the contract's required keys."""
    result = _run("--case", str(CASES / "c04_block_contraindicated.json"))
    assert result.returncode == 0, result.stderr
    document = json.loads(result.stdout)

    for key in ("case_id", "verdict", "findings", "coverage_complete", "table_version"):
        assert key in document
    assert document["verdict"] == "BLOCK"
    assert all({"rule_id", "code", "severity", "statement", "table_version"} <= set(f) for f in document["findings"])


def test_cli_malformed_input_exits_2():
    """REQ-F-008: malformed input is a typed error, not a traceback."""
    result = _run("--case", str(CASES / "malformed.json"))
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "MALFORMED_CASE"


def test_cli_missing_file_exits_2(tmp_path):
    """[REQ-F-008] cli missing file exits 2."""
    result = _run("--case", str(tmp_path / "nope.json"))
    assert result.returncode == 2


def test_cli_advisory_flag():
    """[REQ-F-008] cli advisory flag."""
    result = _run("--case", str(CASES / "c01_approve_single.json"), "--advisory")
    assert result.returncode == 0
    assert "NOT FOR CLINICAL USE" in json.loads(result.stdout)["advisory"]


def test_cli_writes_audit_record(tmp_path):
    """REQ-F-007: CLI path writes the audit record too, not just the library path."""
    audit = tmp_path / "audit.jsonl"
    result = _run("--case", str(CASES / "c01_approve_single.json"), "--audit", str(audit))
    assert result.returncode == 0, result.stderr
    assert audit.exists()
    assert len(audit.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize("fixture,expected", [
    ("c01_approve_single.json", "APPROVE"),
    ("c04_block_contraindicated.json", "BLOCK"),
    ("c05_block_ceiling.json", "BLOCK"),
    ("c14_hold_unknown_drug.json", "HOLD"),
    ("c12_hold_coverage_hole.json", "HOLD"),
    ("c11_hold_missing_egfr_renal.json", "HOLD"),
])
def test_cli_verdicts(fixture, expected):
    """[REQ-F-008] The six fixtures pin the six interesting outcome classes."""
    result = _run("--case", str(CASES / fixture))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verdict"] == expected
