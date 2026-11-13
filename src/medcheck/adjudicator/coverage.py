"""Coverage assessment: the fail-closed heart of INV-001.

Two ways to be uncovered, both must hold:
  1. a drug with no dose row (we cannot check its ceiling)
  2. a pair declared a hole in the table (we have not assessed it)

Neither produces APPROVE, and neither produces silence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from ..contracts import CODE_COVERAGE_GAP, Finding, Medication, Severity
from ..rules.loader import RuleTables


@dataclass
class CoverageReport:
    unknown_drugs: list[str] = field(default_factory=list)
    holes: list[tuple[str, str]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.unknown_drugs and not self.holes


def assess(
    medications: tuple[Medication, ...] | list[Medication],
    tables: RuleTables,
) -> CoverageReport:
    report = CoverageReport()
    names = sorted({med.name_canonical for med in medications if med.name_canonical})

    for name in names:
        if not tables.covers_drug(name):
            report.unknown_drugs.append(name)
            report.findings.append(
                Finding(
                    rule_id="SYS-COVERAGE-001",
                    code=CODE_COVERAGE_GAP,
                    severity=Severity.MAJOR,
                    statement=(
                        f"{name} is not in the rule tables; no ceiling or interaction "
                        "check is possible, so the case is escalated rather than approved"
                    ),
                    table_version=tables.version,
                )
            )

    for first, second in combinations(names, 2):
        if tables.is_hole(first, second):
            report.holes.append((first, second))
            report.findings.append(
                Finding(
                    rule_id="SYS-COVERAGE-001",
                    code=CODE_COVERAGE_GAP,
                    severity=Severity.MAJOR,
                    statement=(
                        f"the pair {first} + {second} is declared unassessed in table "
                        f"{tables.version}; interaction status unknown"
                    ),
                    table_version=tables.version,
                )
            )

    return report
