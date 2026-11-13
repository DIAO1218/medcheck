"""Schema gate for the requirements registry.

Used by .github/workflows/ci.yml (gate 3) and runnable locally:

    python scripts/validate_requirements.py
    python scripts/validate_requirements.py --registry path/to/requirements.yaml

Exit codes:
    0  registry is valid
    1  registry violates the schema or a cross-field rule
    2  the registry or schema file could not be read/parsed

Beyond the JSON Schema, this gate enforces rules a schema cannot express:
  * requirement ids are unique
  * every `source` reference resolves to a declared source
  * every invariant is zero-tolerance and carries a fit criterion with a
    falsifiable quantity
  * MUST requirements that gate a safety path name an enforcing component
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "docs" / "req" / "requirements.yaml"
DEFAULT_SCHEMA = ROOT / "docs" / "req" / "req-schema.json"

QUANTITY = re.compile(r"\d")
SAFETY_PREFIXES = ("REQ-I-", "REQ-S-")


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle) if path.suffix == ".json" else yaml.safe_load(handle)


def check(registry: dict, schema: dict) -> list[str]:
    errors: list[str] = []

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(registry), key=lambda e: list(e.path)):
        where = "/".join(str(part) for part in error.path) or "<root>"
        errors.append(f"schema: {where}: {error.message}")

    requirements = registry.get("requirements") or []
    declared_sources = {source["id"] for source in registry.get("sources") or []}

    seen: set[str] = set()
    for index, requirement in enumerate(requirements):
        req_id = requirement.get("id", f"<index {index}>")
        if req_id in seen:
            errors.append(f"duplicate id: {req_id}")
        seen.add(req_id)

        source = requirement.get("source")
        if source and source not in declared_sources:
            errors.append(f"{req_id}: source {source} is not declared under sources")

        if requirement.get("type") == "invariant":
            if requirement.get("zero_tolerance") is not True:
                errors.append(f"{req_id}: invariant must set zero_tolerance: true")
            criterion = requirement.get("fit_criterion", "")
            if not QUANTITY.search(criterion):
                errors.append(f"{req_id}: invariant fit criterion has no falsifiable quantity")

        if (
            requirement.get("priority") == "must"
            and str(req_id).startswith(SAFETY_PREFIXES)
            and not requirement.get("component")
        ):
            errors.append(f"{req_id}: safety MUST requirement must name its enforcing component")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the requirements registry.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)

    try:
        registry = load(args.registry)
        schema = load(args.schema)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = check(registry, schema)
    if errors:
        print(f"FAIL: {len(errors)} problem(s) in {args.registry.name}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    total = len(registry["requirements"])
    invariants = sum(1 for r in registry["requirements"] if r["type"] == "invariant")
    print(f"PASS: {total} requirements ({invariants} invariants) validate against {args.schema.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
