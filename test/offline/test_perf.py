"""REQ-P-001 — deterministic adjudication latency."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from medcheck.pipeline import process_case

CASES = Path(__file__).resolve().parents[1] / "fixtures" / "cases"
BUDGET_MS = 50.0


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = max(0, int(round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def test_adjudication_p95_within_50ms(tables):
    """REQ-P-001: p95 <= 50 ms over 1000 cases with warm tables."""
    case = json.loads((CASES / "c04_block_contraindicated.json").read_text(encoding="utf-8"))

    # warm the caches so the measurement is the adjudicator, not the filesystem
    for _ in range(5):
        process_case(case, tables=tables)

    samples: list[float] = []
    for _ in range(1000):
        started = time.perf_counter()
        process_case(case, tables=tables)
        samples.append((time.perf_counter() - started) * 1000)

    p95 = _p95(samples)
    assert p95 <= BUDGET_MS, f"p95 {p95:.2f} ms exceeds {BUDGET_MS} ms (median {statistics.median(samples):.2f} ms)"
