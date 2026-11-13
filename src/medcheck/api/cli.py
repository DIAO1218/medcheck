"""Command-line entry point (REQ-F-008).

Exit codes are part of the contract:
    0  adjudication produced
    2  malformed input (typed error object on stdout)
    3  invariant abort / table invalid (no result document may exist)
    4  audit unavailable (result deliberately withheld)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..audit.log import AuditLog
from ..contracts import (
    AuthorityViolation,
    CeilingAssertionError,
    MedCheckError,
    TableInvalid,
    UnresolvableFinding,
)
from ..pipeline import process_case

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_INVARIANT = 3
EXIT_AUDIT = 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medcheck",
        description="Adjudicate a medication case against pinned rule tables. NOT FOR CLINICAL USE.",
    )
    parser.add_argument("--case", required=True, type=Path, help="case JSON file")
    parser.add_argument("--rules-dir", type=Path, default=None, help="override rule table directory")
    parser.add_argument("--audit", type=Path, default=None, help="audit log path (append-only)")
    parser.add_argument("--advisory", action="store_true", help="include advisory text in the output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
        if not isinstance(case, dict):
            raise ValueError("case file must contain a JSON object")
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": "MALFORMED_CASE", "detail": str(exc)}))
        return EXIT_INPUT

    audit = AuditLog(args.audit) if args.audit else None

    try:
        from ..rules.loader import get_tables

        tables = get_tables(args.rules_dir) if args.rules_dir else get_tables()
        outcome = process_case(case, tables=tables, audit=audit)
    except (AuthorityViolation, CeilingAssertionError, UnresolvableFinding, TableInvalid) as exc:
        print(json.dumps({"error": "INVARIANT_VIOLATION", "detail": str(exc)}))
        return EXIT_INVARIANT
    except MedCheckError as exc:
        print(json.dumps({"error": "MEDCHECK_ERROR", "detail": str(exc)}))
        return EXIT_INPUT
    except OSError as exc:
        print(json.dumps({"error": "AUDIT_UNAVAILABLE", "detail": str(exc)}))
        return EXIT_AUDIT

    document = outcome.result.to_dict()
    if args.advisory:
        document["advisory"] = outcome.advisory
    print(json.dumps(document, indent=2, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
