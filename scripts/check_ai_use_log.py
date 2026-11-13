"""Gate 6 — AI-use log gate (REQ-G-001).

A change to code or prompts that does not update the AI-use log is blocked. The
log is how a reader reconstructs which agent did what, on whose instruction; a
missing entry breaks that chain silently, which is worse than a failing build.

    python scripts/check_ai_use_log.py --changed src/medcheck/rules/dose.py
    python scripts/check_ai_use_log.py --base origin/main
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = Path("docs/ai-use-log.yaml")
TRIGGERS = ("src/", "prompts/")
EXEMPT = ("src/medcheck/__init__.py",)


def triggers_log(changed: list[str]) -> bool:
    return any(
        path.startswith(TRIGGERS) and not path.endswith(EXEMPT) for path in changed
    )


def violations(changed: list[str]) -> list[str]:
    if not triggers_log(changed):
        return []
    if any(path == LOG.as_posix() for path in changed):
        return []
    touched = sorted(path for path in changed if path.startswith(TRIGGERS))
    return [
        "code or prompt changed without updating docs/ai-use-log.yaml: "
        + ", ".join(touched[:5])
    ]


def changed_from_git(base: str) -> list[str]:
    output = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed", nargs="*", default=None)
    parser.add_argument("--base", default=None)
    args = parser.parse_args(argv)

    changed = args.changed if args.changed is not None else (
        changed_from_git(args.base) if args.base else []
    )

    problems = violations([path.replace("\\", "/") for path in changed])
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"PASS: AI-use log gate ({len(changed)} changed file(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
