"""Permission-model consistency gate (REQ-G-002 support).

Checks that the machine-readable model still says what the architecture says:
deny-by-default, human-only surfaces present, safety-critical paths real, and no
role able to write a human-only file.

    python scripts/check_permissions_sync.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from medcheck.api.permissions import check, load_policy  # noqa: E402

REQUIRED_HUMAN_ONLY = ("AGENTS.md", "architecture-blueprint.md", ".opencode/**", ".agent/**")
REQUIRED_SAFETY = ("src/medcheck/adjudicator", "src/medcheck/rules", "src/medcheck/privacy", "src/medcheck/audit")


def violations(policy: dict | None = None) -> list[str]:
    policy = policy or load_policy()
    problems: list[str] = []

    if policy.get("default") != "deny":
        problems.append("permission model must be deny-by-default")

    human_only = policy.get("human_only_write", [])
    for required in REQUIRED_HUMAN_ONLY:
        if required not in human_only:
            problems.append(f"'{required}' is missing from human_only_write")

    for role in policy.get("roles", {}):
        for path in ("AGENTS.md", ".opencode/rules.md", "docs/architecture/adr/999-x.md"):
            if check(path, role, "write", policy).allowed:
                problems.append(f"role '{role}' can write human-only path '{path}'")

    for path in REQUIRED_SAFETY:
        if not (ROOT / path).is_dir():
            problems.append(f"safety-critical path does not exist: {path}")

    guarded = policy.get("guards", {}).get("safety_critical_paths", [])
    for path in REQUIRED_SAFETY:
        if not any(path in pattern for pattern in guarded):
            problems.append(f"safety-critical path not guarded: {path}")

    return problems


def main() -> int:
    problems = violations()
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print("PASS: permission model is deny-by-default and consistent with the blueprint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
