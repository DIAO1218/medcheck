"""Gates 1 and 6 — test-approval gate and safety-critical ADR gate (REQ-G-003, G-004).

Both gates read `docs/test-approvals.yaml`, the ledger of approved test plans:

    modules:
      - module: rules
        approved: true
        approved_by: "Zhou, A"
        approved_at: "2026-11-14"
        tests: ["test/offline/test_dose.py::test_over_limit_blocked"]
        adr: null            # required for safety-critical modules

A module is derivable from any path under src/medcheck/<module>/.

    python scripts/check_test_approval.py --changed src/medcheck/rules/dose.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "test-approvals.yaml"
SAFETY_CRITICAL = {"adjudicator", "rules", "privacy", "audit"}


def module_of(path: str) -> str | None:
    """src/medcheck/<module>/... -> <module>; contracts.py and pipeline.py -> core."""
    parts = path.replace("\\", "/").split("/")
    if len(parts) < 3 or parts[0] != "src" or parts[1] != "medcheck":
        return None
    if len(parts) == 3:
        return "core"
    return parts[2]


def load_ledger(path: Path = LEDGER) -> dict:
    if not path.is_file():
        return {"modules": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"modules": []}


def violations(changed: list[str], ledger: dict | None = None) -> list[str]:
    ledger = ledger if ledger is not None else load_ledger()
    approved = {entry["module"]: entry for entry in ledger.get("modules", []) if entry.get("approved")}

    problems: list[str] = []
    for module in sorted({m for m in (module_of(path) for path in changed) if m}):
        entry = approved.get(module)
        if entry is None:
            problems.append(f"no approved test record for module '{module}' (gate 1)")
            continue
        if not entry.get("tests"):
            problems.append(f"module '{module}' approval names no tests (gate 1)")
        if module in SAFETY_CRITICAL and not entry.get("adr"):
            problems.append(
                f"module '{module}' is safety-critical and the change has no ADR id (gate 6)"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed", nargs="*", default=[])
    args = parser.parse_args(argv)

    problems = violations(args.changed)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"PASS: test-approval + ADR gates ({len(args.changed)} changed file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
