"""Fail when a document claims a test count the suite does not have.

The drift this catches is real: the suite went from 165 to 199 to 210 while the
README, the report and the compliance matrix each kept their own number. Nobody
noticed because nothing compared prose against `pytest --collect-only`.

    python scripts/check_test_count.py              # check, exit 1 on drift
    python scripts/check_test_count.py --actual 210 # check against a hypothetical count
    python scripts/check_test_count.py --list       # print every claim found

What counts as a claim: a number immediately followed by a test noun
("199 offline tests", "199 passed", "199 项测试"), in documents that describe the
current state. Historical runs are skipped on purpose — a mutation table that
says "baseline: 199 passed" is a record of a past measurement, not a claim about
today.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Documents that describe the system as it is now.
CURRENT_STATE_DOCS = [
    "README.md",
    "README.en.md",
    "项目简介.md",
    "Report.md",
    "Report.zh.md",
    "SUBMISSION-CHECKLIST.md",
    "AGENTS.md",
    "docs/compliance-matrix.md",
]

#: Whole trees that describe current state.
CURRENT_STATE_TREES = ["docs/zh"]

#: Files whose numbers are historical records, never current claims.
SKIP_FILES = {
    "docs/zh/transcript-summaries.zh.md",
    "docs/mutation-results-M4.md",
    "docs/zh/mutation-results-M4.zh.md",
    "docs/zh/task-mutation-checks.zh.md",
    "docs/bug-diary.md",
    "docs/architecture/evaluation-logbook.md",
    "docs/architecture/evaluation-table.md",
    "docs/debt-register.md",
}

#: Lines that record a past measurement rather than the present state.
SKIP_LINE = re.compile(
    r"baseline|基线|passed in|before each|历史|at the time|that day|2026-1[01]-\d\d"
    r"|\bred\b|\bfailed?\b|失败|变异|mutation|adversarial|载荷"
    r"|test functions?|测试函数|test cases?|test files?",
    re.IGNORECASE,
)

EN = re.compile(
    r"(?<![\d.])(\d{2,4})\s+(?:deterministic\s+|offline\s+|passing\s+)?tests?\b"
    r"(?!\s+(?:functions?|cases?|files?))",
    re.IGNORECASE,
)
EN_PASSED = re.compile(r"(?<![\d.])(\d{2,4})\s+passed\b", re.IGNORECASE)
ZH = re.compile(r"(?<![\d.])(\d{2,4})\s*(?:项|个)\s*(?:确定性|离线)?\s*测试")
ZH_SUITE = re.compile(r"(?<![\d.])(\d{2,4})\s*项(?:确定性)? (?:离线)?测试")


def collect_count() -> int:
    """Number of tests pytest would run offline, asked from pytest itself."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test/offline", "--collect-only", "-q"],
        check=False, cwd=ROOT, capture_output=True, text=True,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout)
    if not match:
        raise SystemExit("could not read the collected test count from pytest")
    return int(match.group(1))


def documents() -> list[Path]:
    paths = [ROOT / name for name in CURRENT_STATE_DOCS if (ROOT / name).is_file()]
    for tree in CURRENT_STATE_TREES:
        base = ROOT / tree
        if base.is_dir():
            paths += sorted(p for p in base.rglob("*.md") if p.is_file())
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in SKIP_FILES]


def claims(path: Path) -> list[tuple[int, int, str]]:
    """(line number, claimed count, line text) for every test-count claim."""
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if SKIP_LINE.search(line):
            continue
        for pattern in (EN, EN_PASSED, ZH, ZH_SUITE):
            for match in pattern.finditer(line):
                found.append((number, int(match.group(1)), line.strip()))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual", type=int, default=None,
                        help="treat this as the real count instead of asking pytest")
    parser.add_argument("--list", action="store_true", help="print every claim found")
    args = parser.parse_args()

    actual = args.actual if args.actual is not None else collect_count()
    total, bad = 0, []
    for path in documents():
        rel = path.relative_to(ROOT).as_posix()
        for line_no, claimed, text in claims(path):
            total += 1
            if args.list:
                mark = "ok " if claimed == actual else "BAD"
                print(f"{mark} {rel}:{line_no}  claims {claimed}  |  {text[:90]}")
            if claimed != actual:
                bad.append((rel, line_no, claimed, text))

    print(f"actual: {actual} tests · claims checked: {total} · mismatches: {len(bad)}")
    if bad:
        for rel, line_no, claimed, text in bad:
            print(f"FAIL {rel}:{line_no} says {claimed}, suite has {actual}")
            print(f"     {text[:120]}")
        return 1
    print("PASS: every current-state document agrees with the suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
