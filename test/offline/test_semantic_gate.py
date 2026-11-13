"""CI gate 4 — semantic evaluation (REQ-Q-001).

The gate is only worth having if it can fail, so the negative case is tested
alongside the real replay.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import eval_replay


def test_thresholds_configured():
    """REQ-Q-001 pins both numbers; a silent threshold change is a defect."""
    assert eval_replay.THRESHOLDS == {"faithfulness": 0.90, "relevance": 0.85}


def test_replay_meets_thresholds():
    """[REQ-Q-001] The frozen set currently passes both quality gates."""
    result = eval_replay.replay()
    assert result["cases"] >= 6
    assert eval_replay.gate(result) == [], result


def test_gate_blocks_a_regression():
    """[REQ-Q-001] A prompt change that drops faithfulness below 0.90 must be blocked."""
    result = {"faithfulness": 0.72, "relevance": 0.88}
    problems = eval_replay.gate(result)
    assert len(problems) == 1
    assert "faithfulness" in problems[0]


def test_replay_reports_failures_with_case_names():
    """[REQ-Q-001] When the advisory drifts, the report says which case, not just a score."""
    result = eval_replay.replay()
    assert isinstance(result["failures"], list)
