"""Maximum daily dose check with renal banding.

The ceiling is computed here and nowhere else. Downstream code may compare
against it, may never recompute or override it (INV-002).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts import (
    CODE_DOSE_CEILING,
    CODE_RENAL_DATA_MISSING,
    CODE_UNIT_UNSUPPORTED,
    Finding,
    Medication,
    NormalizedDose,
    Severity,
    UnconvertibleUnit,
    UnsupportedFrequency,
)
from .loader import RuleTables
from .units import mg, to_mg_per_day


@dataclass
class DoseCheck:
    findings: list[Finding] = field(default_factory=list)
    normalized: list[NormalizedDose] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    missing_renal: list[str] = field(default_factory=list)


def check(
    medications: tuple[Medication, ...] | list[Medication],
    egfr: float | None,
    tables: RuleTables,
) -> DoseCheck:
    result = DoseCheck()
    # eGFR only narrows the ceiling for drugs that are renally cleared. For the
    # rest, the full ceiling applies even when eGFR is missing -- holding every
    # non-renal drug on a missing creatinine would make APPROVE unreachable.
    unrestricted = tables.renal_band(10_000.0)

    for medication in medications:
        row = tables.dose_row(medication.name_canonical)
        if row is None:
            continue  # coverage.py owns the unknown-drug path

        if row.get("renal_sensitive") and egfr is None:
            # P-12: do not evaluate the ceiling against a guessed renal band. A
            # BLOCK would assert "this dose is too high", which we do not know;
            # a HOLD asserts "we do not know", which is true. Skip the comparison
            # entirely and escalate.
            result.missing_renal.append(medication.name_canonical)
            result.findings.append(
                Finding(
                    rule_id="SYS-RENAL-001",
                    code=CODE_RENAL_DATA_MISSING,
                    severity=Severity.MAJOR,
                    statement=(
                        f"{medication.name_canonical} is renally cleared and no eGFR was "
                        "recorded; the dose ceiling was not evaluated and the case is held"
                    ),
                    table_version=tables.version,
                )
            )
            continue

        band = tables.renal_band(egfr) if row.get("renal_sensitive") else unrestricted

        try:
            daily = to_mg_per_day(medication, tables)
        except (UnconvertibleUnit, UnsupportedFrequency) as exc:
            result.unsupported.append(medication.name_canonical)
            result.findings.append(
                Finding(
                    rule_id="SYS-UNIT-001",
                    code=CODE_UNIT_UNSUPPORTED,
                    severity=Severity.MODERATE,
                    statement=(
                        f"{medication.name_canonical}: dose could not be normalised "
                        f"({exc}); ceiling not evaluated for this drug"
                    ),
                    table_version=tables.version,
                )
            )
            continue

        ceiling = float(row["max_mg_per_day"]) * float(band["factor"])
        result.normalized.append(
            NormalizedDose(
                medication=medication.name_canonical,
                mg_per_day=daily,
                ceiling_mg_per_day=ceiling,
                renal_band=str(band["name"]),
            )
        )

        # Tolerance absorbs binary float noise (e.g. 3 x 0.0833), not rounding of
        # clinical values: 1e-9 relative, never a "close enough" band.
        if daily > ceiling * (1 + 1e-9):
            result.findings.append(
                Finding(
                    rule_id=str(row["rule_id"]),
                    code=CODE_DOSE_CEILING,
                    severity=Severity.MAJOR,
                    statement=(
                        f"{medication.name_canonical} at {mg(daily)}/day exceeds the "
                        f"{band['name']} ceiling of {mg(ceiling)}/day"
                    ),
                    table_version=tables.version,
                )
            )

    return result
