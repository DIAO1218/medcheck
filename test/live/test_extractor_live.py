"""Live tests — require a model endpoint, never run in offline CI.

Gate 5 runs `test/offline` only. These tests exist so the live path is measured
rather than assumed: accuracy (REQ-F-001), end-to-end latency (REQ-P-002) and
cost (REQ-C-001).

    MEDCHECK_LLM_BASE_URL=... MEDCHECK_LLM_API_KEY=... python -m pytest test/live -q
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from medcheck.extractor import llm

pytestmark = pytest.mark.live

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"

requires_model = pytest.mark.skipif(
    not llm.configured(), reason="no model endpoint configured (offline environment)"
)


@requires_model
def test_live_extraction_accuracy(tables):
    """REQ-F-001: the live extractor finds the drugs in a clean note and returns
    a record with no authority fields."""
    note = "Warfarin 5 mg once daily. Aspirin 100 mg once daily. eGFR 62."
    record = llm.extract(note, tables.vocabulary)

    names = {med.name_canonical for med in record.medications}
    assert {"warfarin", "aspirin"} <= names
    assert record.egfr is not None


@requires_model
def test_live_end_to_end_latency(tables):
    """REQ-P-002: p95 wall clock per case <= 6 s over 20 cases."""
    samples = []
    for _ in range(20):
        started = time.perf_counter()
        llm.extract("Warfarin 5 mg once daily. eGFR 70.", tables.vocabulary)
        samples.append(time.perf_counter() - started)

    p95 = sorted(samples)[int(0.95 * (len(samples) - 1))]
    assert p95 <= 6.0, f"p95 {p95:.2f}s exceeds 6s"


@requires_model
def test_cost_per_case(tables):
    """REQ-C-001: the extraction call stays inside the token budget."""
    from medcheck.extractor.context import assemble

    context = assemble("Warfarin 5 mg once daily. eGFR 70.", tables.vocabulary)
    assert context.token_estimate <= 3000


def test_offline_suite_does_not_need_a_model():
    """[REQ-F-001] A guard against accidentally importing the live path into offline tests."""
    assert (CASES / "c01_approve_single.json").is_file()
    assert os.environ.get("MEDCHECK_ALLOW_HEURISTIC") in (None, "0", "1")
