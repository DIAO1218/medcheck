"""Deterministic offline extractor.

Decision: ADR-001 section 5 (perception only; the model layer implements the same contract).
Requirement: REQ-F-001.

Purpose is not to be good at language -- it is to give CI a *real* input path so
the deterministic core is tested end to end without a model. The live extractor
(`llm.py`) must produce the same contract; anything it can express that this one
cannot is a coverage question, not a test problem.
"""

from __future__ import annotations

import re

from ..contracts import ExtractionRecord, Medication

VERSION = "heuristic-v1"

_DOSE = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z\-]{2,})\s+(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>mcg|mg|g)\b",
    re.IGNORECASE,
)
_EGFR = re.compile(r"eGFR\s*(?:of|is|:|=)?\s*(?P<value>\d+(?:\.\d+)?)", re.IGNORECASE)

#: frequency phrases the heuristic understands, longest first so "three times
#: daily" wins over "daily".
_FREQUENCIES: tuple[str, ...] = (
    "four times daily",
    "three times daily",
    "twice daily",
    "once daily",
    "q24h",
    "q12h",
    "q8h",
    "q6h",
    "mane",
    "nocte",
    "qds",
    "tds",
    "bid",
    "tid",
    "qid",
    "bd",
    "od",
)


def extract(note: str, vocabulary: tuple[str, ...] | list[str] = ()) -> ExtractionRecord:
    vocab = {name.lower() for name in vocabulary}
    medications: list[Medication] = []
    unparsed: list[str] = []
    seen: set[str] = set()

    for match in _DOSE.finditer(note):
        raw_name = match.group("name").strip()
        canonical = raw_name.lower()
        if canonical in seen:
            continue
        seen.add(canonical)
        tail = note[match.end() : match.end() + 40]
        frequency, matched_phrase = _find_frequency(tail)

        if frequency is None:
            unparsed.append(f"{canonical}: frequency")
        if canonical not in vocab:
            # Not an error at extraction time: coverage will escalate it. The
            # extractor must not decide that an unknown word is not a drug.
            unparsed.append(f"{canonical}: unknown vocabulary")

        medications.append(
            Medication(
                name_raw=raw_name,
                name_canonical=canonical,
                dose_value=float(match.group("value")),
                dose_unit=match.group("unit").lower(),
                frequency_text=matched_phrase,
                route=None,
            )
        )

    egfr_match = _EGFR.search(note)
    egfr = float(egfr_match.group("value")) if egfr_match else None

    return ExtractionRecord(
        medications=tuple(medications),
        egfr=egfr,
        unparsed=tuple(sorted(set(unparsed))),
        prompt_version=VERSION,
    )


def _find_frequency(tail: str) -> tuple[str | None, str | None]:
    lowered = tail.lower()
    for phrase in _FREQUENCIES:
        index = lowered.find(phrase)
        if index != -1:
            return phrase, phrase
    return None, None
