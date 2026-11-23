"""Self-tests for the blocking gates (REQ-G-001, REQ-G-003, REQ-G-004).

A gate is only a gate if a violating change fails it. Each test here constructs
the violation instead of trusting the README.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_ai_use_log
import check_test_approval


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
# gate 1 — test approval and the ADR checks
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
    """[REQ-G-004] Gate 1: safety-critical modules need an ADR id, not just an approval."""
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "rules", "adr": None}]}
    problems = check_test_approval.violations(["src/medcheck/rules/dose.py"], ledger=ledger)
    assert any("no ADR id" in problem for problem in problems)


def test_safety_path_with_adr_passes():
    """[REQ-G-004] safety path with a *fresh* ADR passes."""
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "rules", "adr": "ADR-002"}]}
    changed = ["src/medcheck/rules/dose.py", "docs/architecture/adr/002-dose-banding.md"]
    assert check_test_approval.violations(changed, ledger=ledger) == []


def test_stale_adr_does_not_authorise_a_safety_change():
    """[REQ-G-004] BUG-0012: citing the baseline ADR forever must not pass.

    This is the exact shape of PR #1: contracts.py rewritten, ledger already says
    `adr: ADR-001` from the baseline, so the old gate said PASS.
    """
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "core", "adr": "ADR-001"}]}
    problems = check_test_approval.violations(["src/medcheck/contracts.py"], ledger=ledger)
    assert any("without a new or amended ADR" in problem for problem in problems)


def test_contracts_py_counts_as_a_safety_path():
    """[REQ-G-004] contracts.py is frozen (AGENTS.md section 3), so it is safety-relevant."""
    assert check_test_approval.is_safety_path("src/medcheck/contracts.py")
    assert check_test_approval.is_safety_path("src/medcheck/adjudicator/verdict.py")
    assert not check_test_approval.is_safety_path("src/medcheck/renderer/template.py")


def test_safety_change_with_new_adr_passes_even_with_stale_ledger_adr():
    """[REQ-G-004] an amended ADR in the diff is what authorises the change."""
    ledger = {"modules": [{**LEDGER["modules"][0], "module": "core", "adr": "ADR-001"}]}
    changed = ["src/medcheck/contracts.py", "docs/architecture/adr/002-recursive-authority-check.md"]
    assert check_test_approval.violations(changed, ledger=ledger) == []


def test_docs_only_change_needs_no_adr():
    """[REQ-G-004] documentation work is not architecture work."""
    assert check_test_approval.violations(["README.md", "docs/zh/README.md"]) == []


def test_module_derivation():
    """[REQ-G-003] The gate must find the module from a path, or it is checking nothing."""
    assert check_test_approval.module_of("src/medcheck/rules/dose.py") == "rules"
    assert check_test_approval.module_of("src/medcheck/contracts.py") == "core"
    assert check_test_approval.module_of("docs/req/requirements.yaml") is None
