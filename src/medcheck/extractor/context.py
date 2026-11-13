"""Layered context assembly for the extractor (ADR-001 section 5).

Six layers, fixed caps, a 2400-token compaction threshold, and one non-negotiable
rule: layer 2 (standing constraints) is re-injected verbatim after any
compaction. A safety instruction that can be compacted away is not a constraint.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TOTAL_BUDGET = 3000
COMPACTION_THRESHOLD = 2400

L1_IDENTITY = (
    "You are the medication extractor for MedCheck. You read a clinical note and "
    "return a JSON record. You do not judge safety, you do not compute doses, and "
    "you do not recommend anything."
)
L2_CONSTRAINTS = (
    "STANDING CONSTRAINTS (non-negotiable): "
    "1) Never output a verdict, severity, dose_mg_per_day, findings, or table_version field. "
    "2) Never invent a medication that is not written in the note. "
    "3) If a field cannot be read, emit it as unparsed instead of guessing. "
    "4) Return JSON only, matching the ExtractionRecord schema."
)
L2_TOKEN = "L2"

CAPS = {"L1": 320, "L2": 180, "L3": 900, "L4": 600, "L5": 400, "L6": 600}


def estimate_tokens(text: str) -> int:
    """Cheap, deterministic estimate: 4 characters per token."""
    return max(1, len(text) // 4)


@dataclass
class AssembledContext:
    payload: str
    token_estimate: int
    layers_compacted: list[str] = field(default_factory=list)
    constraint_reinjected: bool = True
    tokens_by_layer: dict[str, int] = field(default_factory=dict)

    @property
    def within_budget(self) -> bool:
        return self.token_estimate <= TOTAL_BUDGET


def assemble(
    note: str,
    vocabulary: tuple[str, ...] | list[str] = (),
    history: tuple[str, ...] | list[str] = (),
    state: str | None = None,
) -> AssembledContext:
    compacted: list[str] = []

    l1 = L1_IDENTITY
    l2 = L2_CONSTRAINTS
    l3 = _vocabulary_layer(vocabulary)
    l4 = "\n".join(list(history)[-4:])
    l5 = state or ""
    l6 = note

    def total() -> int:
        return sum(estimate_tokens(part) for part in (l1, l2, l3, l4, l5, l6))

    # Compaction in reverse priority: L4, then L3, then L5. L1/L2/L6 are never
    # compacted -- truncating clinical text could drop a drug (P-04 / O-11).
    if total() > COMPACTION_THRESHOLD and l4:
        l4 = "\n".join(list(history)[-2:])
        compacted.append("L4")

    if total() > COMPACTION_THRESHOLD and l3:
        l3 = _vocabulary_layer(vocabulary, limit=40)
        compacted.append("L3")

    if total() > COMPACTION_THRESHOLD and l5:
        l5 = _summarise_state(l5)
        compacted.append("L5")

    payload = "\n\n".join(
        part
        for part in (
            f"[L1 identity]\n{l1}",
            f"[L3 vocabulary]\n{l3}" if l3 else "",
            f"[L4 history]\n{l4}" if l4 else "",
            f"[L5 state]\n{l5}" if l5 else "",
            # L2 immediately before the task: post-compaction restoration.
            f"[L2 {L2_TOKEN} constraints]\n{l2}",
            f"[L6 task]\n{l6}",
        )
        if part
    )

    return AssembledContext(
        payload=payload,
        token_estimate=estimate_tokens(payload),
        layers_compacted=compacted,
        constraint_reinjected=L2_CONSTRAINTS in payload,
        tokens_by_layer={
            "L1": estimate_tokens(l1),
            "L2": estimate_tokens(l2),
            "L3": estimate_tokens(l3),
            "L4": estimate_tokens(l4),
            "L5": estimate_tokens(l5),
            "L6": estimate_tokens(l6),
        },
    )


def _vocabulary_layer(vocabulary: tuple[str, ...] | list[str], limit: int = 120) -> str:
    items = list(vocabulary)[:limit]
    return "known drug names: " + ", ".join(items)


def _summarise_state(state: str) -> str:
    lines = [line for line in state.splitlines() if line.strip()]
    return "\n".join(lines[:3]) + ("\n..." if len(lines) > 3 else "")
