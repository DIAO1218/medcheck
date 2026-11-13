"""Append-only, hash-chained audit log (REQ-F-007).

Decision: ADR-001 section 4 (the audit record is a byproduct of the computation).
Supports INV-005: a verdict is only trustworthy if it can be reconstructed.

Two properties are tested rather than assumed:
  * there is no update path -- `update_record` exists only to refuse (and to let
    the tamper test prove the refusal);
  * any edit to the file breaks `verify()` because each record hashes the previous
    record's hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from ..contracts import AuditImmutableError, AuditRecord, AuditTamperError, MedCheckError

GENESIS = "0" * 64


def _hash_record(record: AuditRecord) -> str:
    payload = json.dumps(
        {
            "case_id": record.case_id,
            "input_hash": record.input_hash,
            "table_version": record.table_version,
            "prompt_version": record.prompt_version,
            "verdict": record.verdict,
            "findings": list(record.findings),
            "prev_hash": record.prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_input(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = GENESIS
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = json.loads(line)["record_hash"]
        return last

    def append(
        self,
        *,
        case_id: str,
        input_hash: str,
        table_version: str,
        prompt_version: str,
        verdict: str,
        findings: tuple[str, ...] | list[str],
    ) -> AuditRecord:
        if self._exists(case_id):
            raise MedCheckError(f"DUPLICATE_CASE: {case_id} already has an audit record")

        record = AuditRecord(
            case_id=case_id,
            input_hash=input_hash,
            table_version=table_version,
            prompt_version=prompt_version,
            verdict=verdict,
            findings=tuple(findings),
            prev_hash=self._last_hash(),
        )
        record = replace(record, record_hash=_hash_record(record))

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        return record

    def _exists(self, case_id: str) -> bool:
        if not self.path.exists():
            return False
        with self.path.open(encoding="utf-8") as handle:
            return any(json.loads(line)["case_id"] == case_id for line in handle if line.strip())

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def verify(self) -> bool:
        previous = GENESIS
        for record in self.records():
            if record["prev_hash"] != previous:
                raise AuditTamperError(f"chain broken at {record['case_id']}: prev_hash mismatch")
            recomputed = hashlib.sha256(
                json.dumps(
                    {
                        "case_id": record["case_id"],
                        "input_hash": record["input_hash"],
                        "table_version": record["table_version"],
                        "prompt_version": record["prompt_version"],
                        "verdict": record["verdict"],
                        "findings": record["findings"],
                        "prev_hash": record["prev_hash"],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            if recomputed != record["record_hash"]:
                raise AuditTamperError(f"record {record['case_id']} does not match its hash")
            previous = record["record_hash"]
        return True

    # -- deliberately absent: any mutation path ---------------------------- #
    def update_record(self, *_: object, **__: object) -> None:
        raise AuditImmutableError(
            "audit records are immutable; corrections are appended as a new record "
            "that supersedes the old one (REQ-F-007)"
        )

    def delete_record(self, *_: object, **__: object) -> None:
        raise AuditImmutableError("audit records cannot be deleted (REQ-F-007)")
