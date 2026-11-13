"""PHI masking (INV-004).

Decision: ADR-001 section 3 (the trust boundary). Invariant: INV-004.

Masking happens before the model boundary. The masker is deliberately allowed to
be *over*-eager: replacing a non-identifier costs nothing, missing one leaks
patient data. The residual scan turns a masking miss into a blocked call (P-21)
rather than a silent leak.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..contracts import MaskingError

TOKEN = "\u2039{tid}\u203a"  # ‹NAME_1› — angle brackets, not brackets, so the
# token can never be confused with a drug name or a dose.

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("NAME", re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?")),
    ("NAME", re.compile(r"\bPatient\s*:\s*[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?")),
    ("HKID", re.compile(r"\b[A-Z]{1,2}\d{6}\(\d|A\)")),
    ("PHONE", re.compile(r"\b(?:\+852[\s-]?)?\d{4}[\s-]?\d{4}\b")),
    ("DOB", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
    ("ADDRESS", re.compile(r"\b(?:Flat|Unit|Room)\s+\d+[A-Za-z]?,\s*\d+\s+[A-Z][a-z]+\s+(?:Street|Road|Avenue)")),
)

#: Patterns that must never survive masking. Used for the residual scan.
_RESIDUAL: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Z]{1,2}\d{6}\(\d|A\)"),
    re.compile(r"\b(?:\+852[\s-]?)?\d{4}[\s-]?\d{4}\b"),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
)

#: Identifier *shapes* we cannot classify with confidence (an ID without its
#: check digit, a long account-like number). We cannot mask what we cannot
#: describe, so a hit here blocks the call instead of guessing (P-20).
_UNCLASSIFIED: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Z]{1,3}\d{6,}\b"),
    re.compile(r"\b\d{9,}\b"),
)


@dataclass(frozen=True)
class MaskedText:
    text: str
    tokens: dict[str, str] = field(default_factory=dict)

    def unmask(self, value: str) -> str:
        out = value
        for token, original in self.tokens.items():
            out = out.replace(TOKEN.format(tid=token), original)
        return out


def mask(text: str, *, strict: bool = True) -> MaskedText:
    """Replace identifiers with typed tokens.

    Args:
        text: raw case note.
        strict: when True, a residual identifier after masking raises
            MaskingError (P-20/P-21). Tests use False only to prove the scan
            catches what masking missed.
    """
    tokens: dict[str, str] = {}
    counters: dict[str, int] = {}
    masked = text

    for kind, pattern in _PATTERNS:
        def _replace(match: re.Match[str], kind: str = kind) -> str:
            counters[kind] = counters.get(kind, 0) + 1
            tid = f"{kind}_{counters[kind]}"
            tokens[tid] = match.group(0)
            return TOKEN.format(tid=tid)

        masked = pattern.sub(_replace, masked)

    if strict:
        residuals = find_identifiers(masked)
        if residuals:
            raise MaskingError(
                f"{len(residuals)} identifier(s) survived masking (first: {residuals[0][0]}); "
                "refusing to send the payload (INV-004)"
            )
        unclassified = unclassified_identifiers(masked)
        if unclassified:
            raise MaskingError(
                f"{len(unclassified)} identifier-shaped token(s) cannot be classified "
                f"(first: {unclassified[0]}); refusing to guess and refusing to send (P-20)"
            )

    return MaskedText(text=masked, tokens=tokens)


def unclassified_identifiers(text: str) -> list[str]:
    """Identifier-shaped tokens that no masking pattern can describe."""
    hits: list[str] = []
    for pattern in _UNCLASSIFIED:
        hits.extend(match.group(0) for match in pattern.finditer(text))
    return hits


def find_identifiers(text: str) -> list[tuple[str, str]]:
    """Return (kind, sample) for every identifier-shaped span in `text`."""
    hits: list[tuple[str, str]] = []
    for pattern in _RESIDUAL:
        for match in pattern.finditer(text):
            hits.append(("residual", match.group(0)))
    return hits


class Scrubber:
    """Redacts identifiers from log records before they are written."""

    def __init__(self) -> None:
        self.hits = 0

    def scrub(self, message: str) -> str:
        out = message
        for pattern in _RESIDUAL:
            def _replace(match: re.Match[str]) -> str:
                self.hits += 1
                return "[REDACTED]"

            out = pattern.sub(_replace, out)
        return out

    def scrub_record(self, record: dict[str, object]) -> dict[str, object]:
        return {
            key: (self.scrub(value) if isinstance(value, str) else value)
            for key, value in record.items()
        }
