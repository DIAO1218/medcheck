"""REQ-C-001 support — layered context assembly and budget."""

from __future__ import annotations

from medcheck.extractor.context import (
    COMPACTION_THRESHOLD,
    L2_CONSTRAINTS,
    TOTAL_BUDGET,
    assemble,
    estimate_tokens,
)


def test_total_budget_within_3000_tokens():
    """REQ-C-001: even with a large vocabulary and history, the payload fits."""
    vocabulary = tuple(f"drug-name-{index:03d}" for index in range(300))
    history = tuple("turn: " + "x" * 2000 for _ in range(4))
    context = assemble("Warfarin 5 mg once daily.", vocabulary, history)

    assert context.token_estimate <= TOTAL_BUDGET
    assert context.within_budget
    assert context.layers_compacted


def test_compaction_reinjects_constraints():
    """[REQ-C-001] ADR-001 section 5: L2 is verbatim in the payload after any compaction."""
    vocabulary = tuple(f"drug-{index}" for index in range(300))
    history = tuple("y " * 1000 for _ in range(4))
    context = assemble("note", vocabulary, history)

    assert context.layers_compacted
    assert L2_CONSTRAINTS in context.payload
    assert context.constraint_reinjected is True


def test_small_input_is_not_compacted():
    """[REQ-C-001] No gratuitous compaction: a short case keeps all six layers intact."""
    context = assemble("Warfarin 5 mg once daily.", ("warfarin", "aspirin"))
    assert context.layers_compacted == []
    assert context.token_estimate < COMPACTION_THRESHOLD


def test_clinical_note_is_never_compacted():
    """[REQ-C-001] P-04 / O-11: L6 is copied whole; over-budget cases are rejected upstream."""
    note = "Warfarin 5 mg once daily. " * 80
    context = assemble(note, ("warfarin",))
    assert context.payload.endswith(note)


def test_estimate_is_deterministic():
    """[REQ-C-001] estimate is deterministic."""
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100
