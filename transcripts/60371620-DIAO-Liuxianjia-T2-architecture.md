# Transcript T2 — Architecture candidate generation and evaluation

- **Session:** T2 · candidate generation, scoring, ADR (D2)
- **Driver:** DIAO Liuxianjia (60371620) · **Annotating:** ⟨M2⟩ ARCH lead, ⟨M5⟩ VERIFY lead
- **Date:** 2026-11-14 · **Baseline:** T1 approved registry (24 reqs, 5 invariants)
- **Sprint:** S0

> **Provenance.** Reconstructed from the S0 build log. Scoring figures are the ones recorded in `docs/architecture/evaluation-table.md`; the challenge to the recall score is E-02/E-03 in `docs/architecture/evaluation-logbook.md`. Condensed where noted.

---

## Setup

> **Human (13:30):** Given the registry, produce at least three candidate architectures for the AI component, score them against our drivers, and recommend one. Do not write code. State the criteria and weights before you score, not after.

## Session

### [13:36] Agent — candidates and weights

> C1 invariant provability ×3, C2 auditability ×2, C3 recall on messy text ×2, C4 cost ×1, C5 latency ×1, C6 build effort ×3, C7 offline CI feasible ×2. Maximum 70.
>
> A1 single model call with structured output; A2 panel of three model passes; A3 RAG over the interaction tables decides; A4 deterministic core with the model at the edges; A5 fine-tuned classifier.

### [13:44] Human intervention — **REJECT** on the weights

> C6 (effort) at ×3 is the largest weight after provability. That is not what we believe; it is what we are afraid of. Effort is recoverable — we can work weekends. Provability is not recoverable at the end of a semester. Re-weight: provability ×3, offline CI ×2, effort ×1.

**Why.** A weight encodes a value judgement. If we weight effort at ×3 we will select the architecture that is cheapest to build, which is A1, which cannot produce the zero-tolerance evidence the registry now demands. The weighting was hiding the conclusion.

**Instead.** Max 60: C1 ×3, C2 ×2, C3 ×2, C4 ×1, C5 ×1, C6 ×1, C7 ×2.

### [13:52] Agent — scoring pass

| Criterion | A1 | A2 | A3 | A4 | A5 |
|---|---|---|---|---|---|
| C1 provability | 1 | 1 | 2 | 5 | 3 |
| C2 auditability | 1 | 1 | 3 | 5 | 2 |
| C3 recall | 5 | 5 | 4 | 4 | 4 |
| C4 cost | 5 | 2 | 3 | 4 | 4 |
| C5 latency | 5 | 2 | 3 | 5 | 5 |
| C6 effort | 5 | 3 | 2 | 3 | 1 |
| C7 offline CI | 1 | 1 | 1 | 5 | 2 |

### [14:01] Human intervention — **CORRECT** on A4/C3

> You gave A4 recall 4. A4's extraction grammar is closed: prose it cannot express becomes a hold. That is worse than A1's recall, not nearly equal. Score it 3 and say why in the justification, or the table is marketing.

**Why.** The table's job is to make the chosen architecture's weakness visible so we design around it (coverage-gap monitoring, table-vocabulary sprints). An inflated score turns a known cost into an invisible one.

**Instead.** A4/C3 = 3, justification: *"honest score: prose the extraction grammar cannot express becomes COVERAGE_GAP. We accept more holds."* Totals become 32 / 24 / 30 / 53 / 35.

### [14:12] Human intervention — **REDIRECT** on A3

> Rejecting A3 as a decision path is right, but discarding retrieval entirely throws away the one thing that helps: drug-name canonicalisation. Keep RAG as a perception aid — the extractor receives the table vocabulary as context — and record the split in the option ledger.

**Why.** Two different uses were being conflated. Retrieval as *decider* introduces silent false negatives (worst failure under driver D1). Retrieval as *context* improves extraction without touching authority. The second is strictly good; discarding it would cost accuracy for no safety gain.

**Instead.** ADR-001 §3 records A3 as "rejected as the decision path, adopted as a sub-component (context layer L3)". `option-ledger.md` O-3 carries the trigger for revisiting.

### [14:20] Human — **REJECT** on the ADR's missing section

> The ADR has the decision and the alternatives. It does not have the conditions that would reopen it, and it does not have our design process. The spec asks for both, and without reopen conditions the decision is unfalsifiable — which is exactly the sin we rejected in T1.

### [14:31] Agent — added §6 reopen conditions and §7 design process

> Five reopen conditions: coverage-gap rate > 20% for two sprints; extraction accuracy < 80% after two prompt iterations; a requirement for probabilistic scoring; cost/latency making even one call infeasible; evidence that holds are routinely ignored.

### [14:38] Human intervention — **REDIRECT**

> Add the negative case explicitly: "the model can do it end-to-end and it's simpler" is *not* a reopen condition. It was already priced into A1's evaluation and lost on verifiability. If we do not write that down, someone will re-litigate it in sprint 3 with a demo.

**Instead.** ADR-001 §6 final paragraph, verbatim.

### [14:47] Human intervention — **REDIRECT** on the layered context design

> The ADR describes six layers but no assembly pipeline, no budget, no compaction threshold, no re-injection policy. The spec asks for all four, and they are the only part of this design that can silently fail: a compaction step that drops the "never emit a verdict" instruction would erode INV-003 with nobody noticing.

**Instead.** ADR §5: layer caps summing to 3000 tokens, 2400 compaction threshold (80%), compaction order L4→L3→L5, L1/L2/L6 never compacted, L2 re-injected verbatim before the task, and `test_context_assembly.py::test_compaction_reinjects_constraints` asserting it.

**Why 80%.** The gap leaves room for the model's own output. Hitting provider-side truncation would drop L2 silently, and L2 is the one layer whose loss changes behaviour.

### [15:02] Human — **APPROVE**

> Approved, with a note for the report: the architecture was not chosen because it is best, but because it is the only one whose invariants we can prove before the deadline. Say that in the ADR.

---

## Outcome

| Item | Result |
|---|---|
| Artefacts | `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md`, `evaluation-table.md`, `option-ledger.md`, `risk-list.md` |
| Candidates | 5 generated, 1 dropped early (A5, no training data), 4 scored |
| Chosen | A4 (53/60); sensitivity analysis shows it wins under every weighting that keeps provability as a criterion |
| What the human caught | a weight that encoded fear; an inflated score that would have hidden the architecture's real weakness; a discarded option worth keeping as a sub-component; two missing ADR sections; a design that could fail silently in compaction |
| What the human missed | that the ADR's "APPROVE only through rule 6" would collide with the real overdose path — found in T5 (BUG-0005) |
| Annotation count | 7 interventions: 2 REJECT, 3 REDIRECT, 1 CORRECT, 1 APPROVE |
