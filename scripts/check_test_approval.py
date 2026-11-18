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

Two distinct ADR checks, because the first one alone was not enough:

  * **Ledger check** — a safety-critical module must name an ADR in the ledger.
  * **Fresh-ADR check** — a change that touches a safety-relevant path must also
    add or amend an ADR *in this change*. Without it, a PR can cite the baseline
    ADR forever and still pass, which is exactly what happened to PR #1
    (BUG-0012: a frozen `contracts.py` rewrite passed with `adr: ADR-001`).

    python scripts/check_test_approval.py --changed src/medcheck/rules/dose.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "test-approvals.yaml"

#: Modules whose ledger entry must name an ADR.
SAFETY_MODULES = {"adjudicator", "rules", "privacy", "audit"}

#: Paths whose change requires an ADR to be added or amended in the same change.
#: `contracts.py` is here because AGENTS.md section 3 freezes it: it carries the
#: authority seam, so editing it is an architectural act even though it is a
#: single file rather than a package.
SAFETY_PATHS = (
    "src/medcheck/contracts.py",
    "src/medcheck/adjudicator/",
    "src/medcheck/rules/",
    "src/medcheck/privacy/",
    "src/medcheck/audit/",
)

ADR_DIR = "docs/architecture/adr/"


def _posix(path: str) -> str:
    return path.replace("\\", "/")


def module_of(path: str) -> str | None:
    """src/medcheck/<module>/... -> <module>; contracts.py and pipeline.py -> core."""
    parts = _posix(path).split("/")
    if len(parts) < 3 or parts[0] != "src" or parts[1] != "medcheck":
        return None
    if len(parts) == 3:
        return "core"
    return parts[2]


def is_safety_path(path: str) -> bool:
    normalised = _posix(path)
    return any(
        normalised == candidate or normalised.startswith(candidate)
        for candidate in SAFETY_PATHS
    )


def adrs_touched(changed: list[str]) -> list[str]:
    return sorted(
        _posix(path)
        for path in changed
        if _posix(path).startswith(ADR_DIR) and _posix(path).endswith(".md")
    )


def load_ledger(path: Path = LEDGER) -> dict:
    if not path.is_file():
        return {"modules": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"modules": []}


def violations(changed: list[str], ledger: dict | None = None) -> list[str]:
    ledger = ledger if ledger is not None else load_ledger()
    approved = {
        entry["module"]: entry for entry in ledger.get("modules", []) if entry.get("approved")
    }

    problems: list[str] = []

    for module in sorted({m for m in (module_of(path) for path in changed) if m}):
        entry = approved.get(module)
        if entry is None:
            problems.append(f"no approved test record for module '{module}' (gate 1)")
            continue
        if not entry.get("tests"):
            problems.append(f"module '{module}' approval names no tests (gate 1)")
        if module in SAFETY_MODULES and not entry.get("adr"):
            problems.append(
                f"module '{module}' is safety-critical and the change has no ADR id (gate 6)"
            )

    safety_hits = sorted({_posix(path) for path in changed if is_safety_path(path)})
    if safety_hits and not adrs_touched(changed):
        problems.append(
            "safety-relevant change without a new or amended ADR under "
            f"{ADR_DIR} (gate 6): " + ", ".join(safety_hits[:3])
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
