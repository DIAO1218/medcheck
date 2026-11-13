"""Semantic evaluation replay (REQ-Q-001, CI gate 4).

Replays a frozen case set and reports two quality scores. These are *proxy*
metrics computed offline, and the report says so plainly:

  * **faithfulness** — share of advisory statements that resolve to a finding or
    a fixed template. A number invented by the renderer lowers this score.
  * **relevance** — share of findings that carry a resolvable rule id and a
    non-empty statement. A finding nobody can act on lowers this score.

They are honest proxies, not a substitute for a human-judged rubric: the 20%
human audit each sprint (REQ-Q-001) is what keeps the proxy from drifting.

    python scripts/eval_replay.py            # report + gate
    python scripts/eval_replay.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from medcheck.adjudicator.verdict import resolve
from medcheck.pipeline import process_case
from medcheck.renderer import template
from medcheck.rules.loader import get_tables

#: Thresholds pinned by REQ-Q-001. A prompt or model change that drops below
#: either one is blocked by CI gate 4.
THRESHOLDS = {"faithfulness": 0.90, "relevance": 0.85}

FROZEN_SET = ROOT / "test" / "fixtures" / "cases"


def replay(case_dir: Path = FROZEN_SET) -> dict:
    tables = get_tables()
    cases = sorted(path for path in case_dir.glob("*.json") if path.name != "malformed.json")

    faithful = 0
    total_statements = 0
    relevant = 0
    total_findings = 0
    failures: list[str] = []

    for path in cases:
        case = json.loads(path.read_text(encoding="utf-8"))
        outcome = process_case(case, tables=tables)

        violations = template.conformance_violations(outcome.result, outcome.advisory)
        statements = [line for line in outcome.advisory.splitlines() if line.strip()]
        total_statements += len(statements)
        faithful += max(0, len(statements) - len(violations))
        if violations:
            failures.append(f"{path.name}: {violations[0]}")

        for finding in outcome.result.findings:
            total_findings += 1
            try:
                resolve(finding, tables)
                if finding.statement.strip():
                    relevant += 1
            except Exception:
                failures.append(f"{path.name}: unresolvable {finding.rule_id}")

    return {
        "cases": len(cases),
        "faithfulness": round(faithful / total_statements, 4) if total_statements else 0.0,
        "relevance": round(relevant / total_findings, 4) if total_findings else 0.0,
        "thresholds": THRESHOLDS,
        "failures": failures[:10],
    }


def gate(result: dict) -> list[str]:
    problems = []
    for metric, threshold in THRESHOLDS.items():
        score = result[metric]
        if score < threshold:
            problems.append(f"{metric} {score} below threshold {threshold}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = replay()
    problems = gate(result)

    if args.json:
        print(json.dumps({**result, "passed": not problems}, indent=2))
    else:
        print(f"cases: {result['cases']}")
        print(f"faithfulness: {result['faithfulness']} (threshold {THRESHOLDS['faithfulness']})")
        print(f"relevance:    {result['relevance']} (threshold {THRESHOLDS['relevance']})")
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}", file=sys.stderr)
        else:
            print("PASS: semantic evaluation gate")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
