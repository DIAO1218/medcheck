"""Verdict composition. The only function in the system that may return APPROVE.

Decision: ADR-001 sections 2 and 4 (authority seam).
Invariants: INV-001, INV-002, INV-003, INV-005.

Ordered evaluation (architecture-blueprint.md section 5); the strongest applicable
verdict wins, and APPROVE is reachable only through rule 6, which requires an
explicit coverage proof and zero findings.
"""

from __future__ import annotations

from ..contracts import (
    CODE_ALL_CHECKS_PASSED,
    CODE_AUTHORITY_VIOLATION,
    CODE_COVERAGE_GAP,
    CODE_DDI_CONTRAINDICATED,
    CODE_DDI_MAJOR,
    CODE_DDI_MINOR_MODERATE,
    CODE_DOSE_CEILING,
    CODE_FIELD_UNPARSED,
    CODE_NO_MEDICATIONS,
    CODE_RENAL_DATA_MISSING,
    CODE_UNIT_UNSUPPORTED,
    SEVERITY_RANK,
    AdjudicationResult,
    CeilingAssertionError,
    Finding,
    NormalizedDose,
    Severity,
    UnresolvableFinding,
    Verdict,
)
from ..rules.loader import RuleTables, get_tables

BLOCK_CODES = frozenset({CODE_DDI_CONTRAINDICATED, CODE_DOSE_CEILING})
HOLD_CODES = frozenset(
    {
        CODE_COVERAGE_GAP,
        CODE_DDI_MAJOR,
        CODE_DDI_MINOR_MODERATE,
        CODE_RENAL_DATA_MISSING,
        CODE_UNIT_UNSUPPORTED,
        CODE_FIELD_UNPARSED,
        CODE_NO_MEDICATIONS,
        CODE_AUTHORITY_VIOLATION,
    }
)

META_RULES = frozenset(
    {
        "SYS-COVERAGE-001",
        "SYS-RENAL-001",
        "SYS-UNIT-001",
        "SYS-FIELD-001",
        "SYS-NO-MEDS-001",
        "SYS-AUTH-001",
        "SYS-PASS-001",
    }
)


def resolve(finding: Finding, tables: RuleTables) -> None:
    """INV-005: a finding must resolve to a rule in the pinned table version."""
    rule_id = finding.rule_id
    if rule_id in META_RULES:
        return
    if rule_id.startswith("DDI-") and any(
        row["rule_id"] == rule_id for row in tables.interactions
    ):
        return
    if rule_id.startswith("DOSE-") and any(
        row.get("rule_id") == rule_id for row in tables.drugs.values()
    ):
        return
    raise UnresolvableFinding(
        f"finding {finding.code} cites '{rule_id}', which is absent from table {tables.version}"
    )


def assert_ceiling(
    normalized: tuple[NormalizedDose, ...] | list[NormalizedDose],
    tables: RuleTables,
    findings: tuple[Finding, ...] | list[Finding] = (),
) -> None:
    """INV-002, two distinct failure modes.

    1. **Ceiling integrity.** The ceiling carried in a result must equal the value
       derived from the pinned table and the recorded renal band. A ceiling that
       was quietly raised to let a dose through is the violation this catches.
    2. **No silent overdose.** A dose above its ceiling may appear in a result
       only alongside an explicit DOSE_CEILING finding. An over-ceiling number
       that nobody reported is the defect.
    """
    codes = {finding.code for finding in findings}

    for dose in normalized:
        row = tables.dose_row(dose.medication)
        if row is None:
            continue
        band = next(
            (item for item in tables.renal_bands if item["name"] == dose.renal_band),
            None,
        )
        if band is None:
            raise CeilingAssertionError(
                f"{dose.medication}: renal band '{dose.renal_band}' is not in table {tables.version}"
            )
        expected = float(row["max_mg_per_day"]) * float(band["factor"])
        if abs(dose.ceiling_mg_per_day - expected) > 1e-9:
            raise CeilingAssertionError(
                f"{dose.medication}: reported ceiling {dose.ceiling_mg_per_day} does not match "
                f"table-derived {expected}; ceilings are not editable at runtime"
            )

    over_ceiling = [
        dose for dose in normalized if dose.mg_per_day > dose.ceiling_mg_per_day * (1 + 1e-9)
    ]
    if over_ceiling and CODE_DOSE_CEILING not in codes:
        offenders = ", ".join(f"{dose.medication}" for dose in over_ceiling)
        raise CeilingAssertionError(
            f"dose above ceiling without a DOSE_CEILING finding: {offenders}; "
            "refusing to emit an unreported overdose"
        )


def _ordered(findings: list[Finding]) -> tuple[Finding, ...]:
    return tuple(sorted(findings, key=lambda item: (-SEVERITY_RANK[item.severity], item.code, item.rule_id)))


def compose(
    *,
    case_id: str,
    findings: list[Finding],
    coverage_complete: bool,
    normalized: list[NormalizedDose],
    table_version: str,
    degraded: str | None = None,
    tables: RuleTables | None = None,
) -> AdjudicationResult:
    active_tables = tables or get_tables()
    for finding in findings:
        resolve(finding, active_tables)
    assert_ceiling(normalized, active_tables, findings)

    codes = {finding.code for finding in findings}

    if codes & BLOCK_CODES:
        verdict = Verdict.BLOCK
    elif codes & HOLD_CODES:
        verdict = Verdict.HOLD
    elif codes:
        # Any finding at all holds. A finding implies something a human should
        # read; approving through a finding is how "minor" becomes a blind spot.
        verdict = Verdict.HOLD
    elif coverage_complete:
        findings = [
            *findings,
            Finding(
                rule_id="SYS-PASS-001",
                code=CODE_ALL_CHECKS_PASSED,
                severity=Severity.INFO,
                statement="all drugs covered, no interaction, no ceiling breach",
                table_version=table_version,
            )
        ]
        verdict = Verdict.APPROVE
    else:
        # Defensive: no findings but incomplete coverage must never approve.
        findings = [
            *findings,
            Finding(
                rule_id="SYS-COVERAGE-001",
                code=CODE_COVERAGE_GAP,
                severity=Severity.MAJOR,
                statement="coverage incomplete; verdict cannot be APPROVE",
                table_version=table_version,
            )
        ]
        verdict = Verdict.HOLD

    return AdjudicationResult(
        case_id=case_id,
        verdict=verdict,
        findings=_ordered(findings),
        coverage_complete=coverage_complete,
        table_version=table_version,
        degraded=degraded,
    )


def _tables_stub(table_version: str) -> RuleTables:
    """Resolution needs rule ids only; the version string is the audit anchor.

    Kept for callers that only hold a version. Prefer passing `tables` to `compose`
    so resolution and scoring provably use the same load.
    """
    from ..rules.loader import get_tables

    return get_tables()
