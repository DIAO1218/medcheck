"""Boundary types for MedCheck.

Decision: ADR-001 (deterministic core at the edges). Invariants: INV-003, INV-005.

Every dataclass here is frozen and crosses at least one module boundary. Changing
a field is an ADR-level change (architecture-blueprint.md section 4.1).

The load-bearing property of this file: `ExtractionRecord` has **no** field for a
verdict, a severity, or a normalized dose. There is no place to put a model's
opinion about safety (REQ-I-003).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


# --------------------------------------------------------------------------- #
# errors
# --------------------------------------------------------------------------- #
class MedCheckError(Exception):
    """Base class for typed, user-facing errors."""


class AuthorityViolation(MedCheckError):
    """A model payload tried to write an authority field (INV-003)."""


class UnconvertibleUnit(MedCheckError):
    """A dose unit has no entry in the conversion table (P-11)."""


class UnsupportedFrequency(MedCheckError):
    """A frequency expression is outside the supported grammar (P-06)."""


class UnresolvableFinding(MedCheckError):
    """A finding cites a rule that is not in the pinned table (INV-005)."""


class CeilingAssertionError(MedCheckError):
    """An output asserted a dose above the applicable ceiling (INV-002)."""


class MaskingError(MedCheckError):
    """An identifier could not be masked, or a residual survived (INV-004)."""


class TableInvalid(MedCheckError):
    """Rule tables failed validation at load time (P-09)."""


class AuditImmutableError(MedCheckError):
    """An attempt was made to rewrite an audit record (REQ-F-007)."""


class AuditTamperError(MedCheckError):
    """The audit hash chain does not verify (REQ-F-007)."""


# --------------------------------------------------------------------------- #
# enumerations
# --------------------------------------------------------------------------- #
class Verdict(StrEnum):
    APPROVE = "APPROVE"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


class Severity(StrEnum):
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    INFO = "info"


SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.MINOR: 1,
    Severity.MODERATE: 2,
    Severity.MAJOR: 3,
    Severity.CONTRAINDICATED: 4,
}

#: Fields that only deterministic code may produce. A model payload containing
#: any of these is rejected before use (INV-003).
FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {"verdict", "severity", "dose_mg_per_day", "table_version", "findings"}
)

#: Finding codes. Kept as constants so tests and policies reference one spelling.
CODE_COVERAGE_GAP = "COVERAGE_GAP"
CODE_DDI_CONTRAINDICATED = "DDI_CONTRAINDICATED"
CODE_DOSE_CEILING = "DOSE_CEILING"
CODE_DDI_MAJOR = "DDI_MAJOR"
CODE_DDI_MINOR_MODERATE = "DDI_MINOR_MODERATE"
CODE_RENAL_DATA_MISSING = "RENAL_DATA_MISSING"
CODE_UNIT_UNSUPPORTED = "UNIT_UNSUPPORTED"
CODE_FIELD_UNPARSED = "FIELD_UNPARSED"
CODE_NO_MEDICATIONS = "NO_MEDICATIONS_FOUND"
CODE_AUTHORITY_VIOLATION = "AUTHORITY_VIOLATION"
CODE_ALL_CHECKS_PASSED = "ALL_CHECKS_PASSED"


# --------------------------------------------------------------------------- #
# extraction side (model-writable, perception only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Medication:
    """One medication as *perceived* in the note.

    Raw text only. `dose_mg_per_day` deliberately does not exist here: it is
    computed by `medcheck.rules.units` from `dose_value`/`dose_unit`/frequency.
    """

    name_raw: str
    name_canonical: str
    dose_value: float | None = None
    dose_unit: str | None = None
    frequency_text: str | None = None
    route: str | None = None

    def __post_init__(self) -> None:
        if not self.name_raw.strip():
            raise ValueError("Medication.name_raw must not be empty")


@dataclass(frozen=True)
class ExtractionRecord:
    """Output of the extractor. Schema-checked, authority-free."""

    medications: tuple[Medication, ...] = ()
    egfr: float | None = None
    unparsed: tuple[str, ...] = ()
    prompt_version: str = "unknown"

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], prompt_version: str) -> ExtractionRecord:
        """Build from a model payload, refusing any authority field.

        Raises:
            AuthorityViolation: if the payload (or any medication entry) carries
                a forbidden field. The whole payload is rejected, not sanitised
                (INV-003: partial trust is not trust).
        """
        _assert_no_authority(payload, where="payload")

        medications: list[Medication] = []
        for raw in payload.get("medications", []) or []:
            if not isinstance(raw, Mapping):
                raise ValueError("each medication must be an object")
            _assert_no_authority(raw, where=f"medications[{len(medications)}]")
            medications.append(
                Medication(
                    name_raw=str(raw.get("name_raw", "")).strip(),
                    name_canonical=str(raw.get("name_canonical") or raw.get("name_raw", "")).strip().lower(),
                    dose_value=_optional_float(raw.get("dose_value")),
                    dose_unit=(str(raw["dose_unit"]).strip().lower() if raw.get("dose_unit") else None),
                    frequency_text=(str(raw["frequency_text"]).strip().lower() if raw.get("frequency_text") else None),
                    route=(str(raw["route"]).strip().lower() if raw.get("route") else None),
                )
            )

        return cls(
            medications=tuple(medications),
            egfr=_optional_float(payload.get("egfr")),
            unparsed=tuple(str(item) for item in (payload.get("unparsed") or [])),
            prompt_version=prompt_version,
        )


def _assert_no_authority(payload: Mapping[str, Any], where: str) -> None:
    offending = FORBIDDEN_AUTHORITY_FIELDS.intersection(payload.keys())
    if offending:
        raise AuthorityViolation(
            f"{where} carries authority field(s) {sorted(offending)}; "
            "only deterministic code may set these (INV-003)"
        )


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


# --------------------------------------------------------------------------- #
# rules and adjudication side (deterministic, authoritative)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Finding:
    rule_id: str
    code: str
    severity: Severity
    statement: str
    table_version: str

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise UnresolvableFinding(f"finding {self.code} has no rule_id (INV-005)")
        if not self.table_version:
            raise UnresolvableFinding(f"finding {self.code} has no table_version (INV-005)")


@dataclass(frozen=True)
class NormalizedDose:
    """Deterministic output of the unit normaliser."""

    medication: str
    mg_per_day: float
    ceiling_mg_per_day: float
    renal_band: str | None = None


@dataclass(frozen=True)
class AdjudicationResult:
    case_id: str
    verdict: Verdict
    findings: tuple[Finding, ...]
    coverage_complete: bool
    table_version: str
    degraded: str | None = None

    @property
    def codes(self) -> list[str]:
        return [finding.code for finding in self.findings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "verdict": self.verdict.value,
            "coverage_complete": self.coverage_complete,
            "table_version": self.table_version,
            "degraded": self.degraded,
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "code": finding.code,
                    "severity": finding.severity.value,
                    "statement": finding.statement,
                    "table_version": finding.table_version,
                }
                for finding in self.findings
            ],
        }


@dataclass(frozen=True)
class AuditRecord:
    case_id: str
    input_hash: str
    table_version: str
    prompt_version: str
    verdict: str
    findings: tuple[str, ...]
    prev_hash: str
    record_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "input_hash": self.input_hash,
            "table_version": self.table_version,
            "prompt_version": self.prompt_version,
            "verdict": self.verdict,
            "findings": list(self.findings),
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
        }


__all__ = [
    "CODE_ALL_CHECKS_PASSED",
    "CODE_AUTHORITY_VIOLATION",
    "CODE_COVERAGE_GAP",
    "CODE_DDI_CONTRAINDICATED",
    "CODE_DDI_MAJOR",
    "CODE_DDI_MINOR_MODERATE",
    "CODE_DOSE_CEILING",
    "CODE_FIELD_UNPARSED",
    "CODE_NO_MEDICATIONS",
    "CODE_RENAL_DATA_MISSING",
    "CODE_UNIT_UNSUPPORTED",
    "FORBIDDEN_AUTHORITY_FIELDS",
    "SEVERITY_RANK",
    "AdjudicationResult",
    "AuditImmutableError",
    "AuditRecord",
    "AuditTamperError",
    "AuthorityViolation",
    "CeilingAssertionError",
    "ExtractionRecord",
    "Finding",
    "MaskingError",
    "MedCheckError",
    "Medication",
    "NormalizedDose",
    "Severity",
    "TableInvalid",
    "UnconvertibleUnit",
    "UnresolvableFinding",
    "UnsupportedFrequency",
    "Verdict",
]
