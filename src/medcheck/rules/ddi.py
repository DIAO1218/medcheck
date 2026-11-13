"""Drug-drug interaction check. Table lookup only: no similarity, no inference.

A pair absent from the table is treated as "no known interaction" *only* if the
pair is not declared a coverage hole (see `data/rules/ddi.yaml`). The hole list
is what keeps absence-of-evidence from becoming evidence-of-absence (INV-001).
"""

from __future__ import annotations

from itertools import combinations

from ..contracts import (
    CODE_DDI_CONTRAINDICATED,
    CODE_DDI_MAJOR,
    CODE_DDI_MINOR_MODERATE,
    Finding,
    Medication,
    Severity,
)
from .loader import RuleTables


def _code_for(severity: str) -> tuple[str, Severity]:
    if severity == "contraindicated":
        return CODE_DDI_CONTRAINDICATED, Severity.CONTRAINDICATED
    if severity == "major":
        return CODE_DDI_MAJOR, Severity.MAJOR
    return CODE_DDI_MINOR_MODERATE, Severity.MODERATE


def check(medications: tuple[Medication, ...] | list[Medication], tables: RuleTables) -> list[Finding]:
    names = sorted({med.name_canonical for med in medications if med.name_canonical})
    findings: list[Finding] = []

    for first, second in combinations(names, 2):
        row = tables.interaction(first, second)
        if row is None:
            continue
        if tables.is_hole(first, second):
            # A hole never suppresses a known interaction; the interaction wins
            # and coverage.py still raises the gap. Both findings are emitted.
            pass
        code, severity = _code_for(str(row["severity"]))
        findings.append(
            Finding(
                rule_id=str(row["rule_id"]),
                code=code,
                severity=severity,
                statement=(
                    f"{first} + {second}: {row.get('effect', 'interaction')} "
                    f"({severity.value})"
                ),
                table_version=tables.version,
            )
        )
    return findings
