"""Self-tests for the blocking gates (REQ-G-001, REQ-G-003, REQ-G-004).

A gate is only a gate if a violating change fails it. Each test here constructs
the violation instead of trusting the README.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_ai_use_log  # noqa: E402
import check_test_approval  # noqa: E402


# --------------------------------------------------------------------------- #
# gate 6 — AI-use log
# --------------------------------------------------------------------------- #
def test_ai_use_log_gate_blocks_unlogged_change():
    """[REQ-G-001] A src/ change without a log update is blocked."""
    problems = check_ai_use_log.violations(["src/medcheck/rules/dose.py"])
    assert len(problems) == 1
    assert "ai-use-log" in problems[0]


def test_ai_use_log_gate_allows_logged_change():
    """[REQ-G-001] ai use log gate allows logged change."""
    problems = check_ai_use_log.violations(
        ["src/medcheck/rules/dose.py", "docs/ai-use-log.yaml"]
    )
    assert problems == []


def test_ai_use_log_gate_ignores_docs_only_change():
    """[REQ-G-001] Documentation work does not need an AI-use entry."""
    assert check_ai_use_log.violations(["docs/debt-register.md", "README.md"]) == []


def test_ai_use_log_gate_requires_log_for_prompt_change():
    """[REQ-G-001] ai use log gate requires log for prompt change."""
    problems = check_ai_use_log.violations(["prompts/prompt_v1.1.yaml"])
    assert problems


# --------------------------------------------------------------------------- #
# gate 1 / gate 6 — test approval and ADR
# --------------------------------------------------------------------------- #
LEDGER = {
    "modules": [
        {
            "module": "renderer",
            "approved": True,
            "approved_by": "Zhou, A",
            "approved_at": "2026-11-14",
            "tests": ["test/offline/test_renderer.py::test_advisory_word_cap"],
            "adr": None,
        }
    ]
}


def test_test_approval_gate_requires_record():
    """[REQ-G-003] Gate 1: a module with no approved test record blocks the change."""
    problems = check_test_approval.violations(
        ["src/medcheck/extractor/heuristic.py"], ledger=LEDGER
    )
    assert problems and "no approved test record" in problems[0]


def test_test_approval_gate_passes_for_approved_module():
    """[REQ-G-003] approval gate passes for approved module."""
    problems = check_test_approval.violations(
        ["src/medcheck/renderer/template.py"], ledger=LEDGER
    )
    assert problems == []


def test_safety_path_change_requires_adr():
    """[REQ-G-004] Gate 6: safety-critical modules need an ADR id, not just an approval."""
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "rules", "adr": None}]}
    problems = check_test_approval.violations(["src/medcheck/rules/dose.py"], ledger=ledger)
    assert any("no ADR id" in problem for problem in problems)


def test_safety_path_with_adr_passes():
    """[REQ-G-004] safety path with adr passes."""
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "rules", "adr": "ADR-001"}]}
    assert check_test_approval.violations(["src/medcheck/rules/dose.py"], ledger=ledger) == []


def test_module_derivation():
    """[REQ-G-003] The gate must find the module from a path, or it is checking nothing."""
    assert check_test_approval.module_of("src/medcheck/rules/dose.py") == "rules"
    assert check_test_approval.module_of("src/medcheck/contracts.py") == "core"
    assert check_test_approval.module_of("docs/req/requirements.yaml") is None
