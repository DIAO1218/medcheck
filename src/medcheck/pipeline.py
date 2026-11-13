"""Case pipeline: the only place the stages are wired together.

Decision: ADR-001 section 2 (stage order is normative).
Invariants touched in order: INV-004 (masking first), INV-001/002/003 (adjudication), INV-005 (citation).

Order matters and is normative (architecture-blueprint.md section 3):
    privacy.mask -> extractor -> coverage -> ddi -> dose -> adjudicator -> audit -> renderer

The renderer runs last because nothing may depend on its output.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .adjudicator import coverage, guard
from .adjudicator.verdict import compose
from .audit.log import AuditLog, hash_input
from .contracts import (
    CODE_FIELD_UNPARSED,
    CODE_NO_MEDICATIONS,
    ExtractionRecord,
    Finding,
    Severity,
    Verdict,
)
from .extractor import heuristic
from .privacy.mask import mask
from .renderer import template
from .rules import ddi, dose
from .rules.loader import RuleTables, get_tables

ExtractorCallable = Callable[[str, tuple[str, ...]], ExtractionRecord]


@dataclass
class CaseOutcome:
    result: object
    advisory: str
    record: ExtractionRecord

    @property
    def verdict(self) -> Verdict:
        return self.result.verdict  # type: ignore[attr-defined]


def process_case(
    case: Mapping[str, object],
    *,
    tables: RuleTables | None = None,
    extractor: ExtractorCallable | None = None,
    audit: AuditLog | None = None,
) -> CaseOutcome:
    tables = tables or get_tables()
    extractor = extractor or heuristic.extract

    case_id = str(case.get("case_id") or "unspecified")
    note = str(case.get("note") or "")
    if not note.strip():
        raise ValueError("case has no note")

    masked = mask(note)
    record = extractor(masked.text, tables.vocabulary)

    findings: list[Finding] = []

    if not record.medications:
        findings.append(
            Finding(
                rule_id="SYS-NO-MEDS-001",
                code=CODE_NO_MEDICATIONS,
                severity=Severity.MAJOR,
                statement="no medication could be read from the note; absence of evidence is not safety",
                table_version=tables.version,
            )
        )

    for item in record.unparsed:
        findings.append(
            Finding(
                rule_id="SYS-FIELD-001",
                code=CODE_FIELD_UNPARSED,
                severity=Severity.MODERATE,
                statement=f"field left unparsed: {item}",
                table_version=tables.version,
            )
        )

    coverage_report = coverage.assess(record.medications, tables)
    findings.extend(coverage_report.findings)
    findings.extend(ddi.check(record.medications, tables))

    dose_check = dose.check(record.medications, record.egfr, tables)
    findings.extend(dose_check.findings)

    result = compose(
        case_id=case_id,
        findings=findings,
        coverage_complete=coverage_report.complete,
        normalized=dose_check.normalized,
        table_version=tables.version,
        tables=tables,
    )
    guard.check_result(result)

    if audit is not None:
        audit.append(
            case_id=case_id,
            input_hash=hash_input(masked.text),
            table_version=tables.version,
            prompt_version=record.prompt_version,
            verdict=result.verdict.value,
            findings=tuple(finding.code for finding in result.findings),
        )

    return CaseOutcome(result=result, advisory=template.render(result), record=record)
