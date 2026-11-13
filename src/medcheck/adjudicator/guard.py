"""Authority guard. The single checkpoint where model output is refused.

Design note: the guard rejects the *whole* payload when it carries an authority
field, rather than deleting the field and continuing. Partial trust is not trust
-- a payload that tried to assert a verdict has told us something about the
model's behaviour, and that information should reach a human, not be silently
cleaned up (INV-003).
"""

from __future__ import annotations

from typing import Any, Mapping

from ..contracts import (
    AdjudicationResult,
    AuthorityViolation,
    FORBIDDEN_AUTHORITY_FIELDS,
    Finding,
    Verdict,
    SEVERITY_RANK,
)


def check_payload(payload: Mapping[str, Any], where: str = "model payload") -> None:
    """Refuse a payload that carries an authority field, at any depth."""
    offending: set[str] = set()
    _collect(payload, offending)
    if offending:
        raise AuthorityViolation(
            f"{where} carries authority field(s) {sorted(offending)}; "
            "verdict, severity and dose are computed by deterministic code only (INV-003)"
        )


def _collect(node: Any, offending: set[str]) -> None:
    if isinstance(node, Mapping):
        offending.update(FORBIDDEN_AUTHORITY_FIELDS.intersection(node.keys()))
        for value in node.values():
            _collect(value, offending)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _collect(item, offending)


def check_findings(findings: tuple[Finding, ...] | list[Finding]) -> None:
    """Every finding must cite a known rule namespace and carry a valid severity."""
    for finding in findings:
        if not finding.rule_id.startswith(_KNOWN_RULE_PREFIXES):
            raise AuthorityViolation(
                f"finding {finding.code} cites rule '{finding.rule_id}', which is outside "
                "the known namespaces (INV-005)"
            )
        SEVERITY_RANK[finding.severity]  # raises KeyError if severity is out of enum


def check_result(result: AdjudicationResult) -> None:
    """A result may only be APPROVE if it carries an explicit pass finding."""
    if result.verdict is Verdict.APPROVE:
        from ..contracts import CODE_ALL_CHECKS_PASSED

        if CODE_ALL_CHECKS_PASSED not in result.codes:
            raise AuthorityViolation(
                "an APPROVE result without an explicit pass finding is unreachable by design"
            )
        if not result.coverage_complete:
            raise AuthorityViolation("APPROVE with incomplete coverage would violate INV-001")


_KNOWN_RULE_PREFIXES: tuple[str, ...] = ("DDI-", "DOSE-", "SYS-")