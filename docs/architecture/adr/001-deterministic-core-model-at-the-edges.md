# ADR-001 — Deterministic adjudication core, model confined to the edges

- **Status:** Accepted
- **Date:** 2026-11-14
- **Deciders:** architecture review (human) · **Consulted:** plan-agent (candidate generation, evaluation) · **Supersedes:** none
- **Requirements touched:** REQ-F-001…F-006, REQ-I-001…I-005, REQ-Q-001, REQ-C-001
- **Invariants locked by this decision:** INV-001 (fail-closed), INV-002 (dose ceiling), INV-003 (authority separation), INV-004 (PHI masking), INV-005 (traceability)

---

## 1. Context

The product must turn a free-text case note into a medication safety verdict. The natural, and cheapest, implementation is one model call: "read this note, tell me if the prescription is safe." That implementation is also the one we cannot verify, cannot bound, and cannot audit — three properties this course, and any safety-adjacent system, requires.

The forces in tension:

- **F1 Language is unstructured.** Dose and frequency are buried in prose ("Lasix 40 mg mane, hold if dry weight down 2 kg"), so *something* has to read natural language.
- **F2 The verdict is a safety decision.** A confident wrong `APPROVE` is the failure mode that matters; a spurious `HOLD` only costs a human a glance. The loss function is asymmetric.
- **F3 Every claim must be auditable.** A reviewer must be able to ask "why?" and get a rule id and a table version, not a paragraph of plausible prose.
- **F4 Budget and latency are real.** REQ-C-001 caps spend at $0.02/case, REQ-P-001 caps deterministic latency at 50 ms p95.
- **F5 CI must run offline.** Gate 5 (regression) and gate 4 (semantic) have to execute on every PR without a live model.

F1 pushes work into the model. F2, F3, F5 push it out. The architecture is a decision about *where to put the seam*.

## 2. Decision

**We place a hard authority seam between "understanding the text" and "deciding about the patient."**

- The model does only **perception**: it maps prose to a schema-checked `ExtractionRecord`. It never sees the rule tables, never emits a verdict, severity, or normalized dose.
- All **judgement** is deterministic: unit normalisation, interaction lookup, dose-ceiling comparison, coverage accounting, verdict composition. Same input + same table version ⇒ byte-identical output.
- The model reappears at the **exit** as a constrained paraphraser, restating findings that already exist. Its output is checked by a conformance test, and nothing downstream reads it.

Three enforcement mechanisms make the seam real rather than aspirational:

1. **Contract-level:** `ExtractionRecord` has no verdict/severity field. There is no place to put a hallucinated verdict (adversarial fixtures prove a model-supplied verdict field is rejected — INV-003).
2. **Type-level:** adjudication result fields are frozen dataclasses written only inside `medcheck.adjudicator`.
3. **CI-level:** an architectural fitness function fails the build if `renderer` or `extractor` writes to `adjudicator` result types, or if any module outside `adjudicator` returns `APPROVE`.

## 3. Alternatives considered

### A1 — Single model call with a structured-output contract ("ask the model for the verdict")

- **For:** cheapest (1 call, ~600 tokens), fastest to build, best language coverage, simplest code.
- **Against:** nothing bounds the failure. Determinism is impossible; the same input can yield `APPROVE` twice and `HOLD` once. No audit trail beyond "the model said so." No offline CI — every regression test would need a live model or a recorded-tape mock, and mock-based tests verify the mock, not the system. Invariants INV-001/002/003 become untestable, i.e. unfalsifiable.
- **Verdict:** rejected. It cannot produce zero-tolerance evidence for any invariant, and the course requires exactly that.

### A2 — Model proposes, model critiques, second model adjudicates ("LLM-as-judge panel")

- **For:** better than A1 on recall of edge cases; still one architecturally simple path; the critique step catches some hallucinations.
- **Against:** adds cost (3× calls, ~$0.06/case — breaks REQ-C-001) and latency (~9 s p95 — breaks REQ-P-002). Two models agreeing is not verification: correlated errors are exactly the ones that hurt. Still non-deterministic, still non-auditable.
- **Verdict:** rejected. Pays 3× for a property it does not acquire.

### A3 — Retrieval-augmented model over the interaction tables (RAG decides)

- **For:** keeps language flexibility, grounds answers in the tables, handles drug names not in the table vocabulary better.
- **Against:** retrieval is a *ranking* operation. Grounding improves plausibility but does not create authority: retrieved-then-paraphrased is still model-authored. Worse, retrieval can silently miss a contraindicated pair — a false negative in a safety check, the exact failure F2 ranks first. And "which rows were retrieved" is not a stable, versionable audit record.
- **Verdict:** rejected as the decision path, **adopted as a sub-component**: the extractor receives the table's drug vocabulary as retrieved context (§5, layer 3) to improve name canonicalisation. Retrieval informs perception; it never decides.

### A4 — Deterministic core with model at the edges (**chosen**)

- **For:** every invariant is provable offline; the deterministic core runs in <5 ms so REQ-P-001 and CI gate 5 are free; the audit record is a byproduct of the computation rather than a narrative of it; model cost drops to one extraction call per case (~$0.004).
- **Against:** the contract between perception and judgement is now a bottleneck — any input form the schema cannot express becomes a `COVERAGE_GAP` and a human review. Extraction errors propagate as coverage gaps rather than being "reasoned around." Table coverage becomes a first-class operational concern.
- **Mitigation:** the coverage-gap metric (§9 of the blueprint) is monitored; gap rate above 20% triggers a table-vocabulary review sprint. This is a *deliberate* cost: we accept more `HOLD`s in exchange for never a silent wrong `APPROVE`.
- **Verdict:** accepted.

## 4. Consequences

**Positive**
- INV-001…005 each have an offline, deterministic, zero-tolerance suite; CI can prove them on every PR.
- Verdicts are reproducible and diffable; a changed verdict between table versions is a reviewable event.
- Cost and latency are dominated by one bounded model call.
- The seam is testable in isolation: `test/offline/test_authority.py` feeds adversarial model payloads and asserts rejection, with no model in the loop.

**Negative / accepted**
- Recall on messy real-world text is worse than A1. Accepted; mitigated by escalation, not by loosening the seam.
- Two artefacts to maintain (extraction contract + rule tables) instead of one prompt. Accepted; both are versioned and diffable, which A1's prompt is not.
- The `COVERAGE_GAP` path will fire often in early sprints. That is the system working.

**Neutral**
- The renderer may or may not use a model; the architecture does not care, because nothing reads its output. v1 uses a deterministic template renderer, with a model-backed variant behind `MEDCHECK_RENDERER=llm` for the semantic evaluation gate.

## 5. Layered context design for the AI component

The extractor is stateless per case but receives a **six-layer context** assembled on every turn. Priority is top-down: when the budget binds, lower layers are compacted first, and layer 2 is re-injected verbatim after any compaction.

| Layer | Content | Typical tokens | Mutability |
|---|---|---|---|
| L1 Identity | role ("you are a medication extractor; you do not judge safety"), output schema, hard prohibitions | 320 | frozen per prompt version |
| L2 Standing constraints | "never emit verdict/severity; never invent a drug not in the note; emit `unparsed` instead of guessing; return JSON only" | 180 | frozen, **re-injected** |
| L3 Retrieved knowledge | canonical drug vocabulary (subset retrieved from `data/rules/*.yaml` matching note tokens), unit table | 900 (cap) | per case |
| L4 Conversation history | previous turns of the same case (correction rounds only) | 600 (cap, rolling) | per session |
| L5 Resumable state | last accepted `ExtractionRecord` + open questions, so an interrupted session resumes without re-reading the whole note | 400 | per session |
| L6 Current task | the masked case note + the specific instruction ("extract; flag anything unparsed") | 600 | per turn |

**Assembly pipeline** (`extractor/context.py`, in this order, each step pure):

1. **Deduplicate** — drop retrieved vocabulary entries already present in L1/L2; collapse repeated history turns by hash.
2. **Prioritise** — L1, L2, L6 are non-droppable; L3 > L5 > L4.
3. **Budget** — cap total at **3000 input tokens** (REQ-C-001). Layer caps above sum to 3000 exactly; the allocator never exceeds a layer cap by borrowing.
4. **Compact** — when projected total > **2400 tokens (80% threshold)**, compact in reverse priority order: truncate L4 to the last 2 turns, then shrink L3 by dropping lowest-similarity entries, then summarise L5 to (accepted fields, open questions). Never compact L1/L2/L6; if L6 alone exceeds its cap, reject the case with `CASE_TOO_LARGE` rather than truncating clinical text.
5. **Assemble** — emit layers in order L1→L6 with explicit delimiters, then **re-inject L2 verbatim** immediately before L6 (post-compaction constraint restoration) and record `layers_compacted` + `constraint_reinjected: true` in the call metadata for the audit trail.

**Why 2400/3000:** the gap leaves headroom for the model's own output and avoids hitting provider-side truncation, which would silently drop L2 — the one layer whose loss changes behaviour. A test (`test/offline/test_context_assembly.py`) asserts that after any compaction path, L2 appears verbatim in the final payload.

## 6. Conditions that would reopen this decision

Reopen only with evidence, not preference. Any one of these triggers a new ADR:

1. Coverage-gap rate stays above 20% for two consecutive sprints **and** a table-vocabulary expansion cannot fix it (i.e. the input distribution genuinely exceeds the closed-world assumption).
2. A measured extraction ceiling: field-level accuracy stays below 80% on accepted inputs after two prompt iterations, making the deterministic core's input too noisy to be useful.
3. A regulatory or course requirement demands a probabilistic risk score rather than a categorical verdict.
4. Cost/latency pressure makes even the single extraction call infeasible (would push toward a local small model — still perception-only, so the seam survives; this reopens the *model choice*, not the seam).
5. Evidence that a `COVERAGE_GAP` escalation is routinely ignored by reviewers, meaning the fail-closed path is nominally safe but operationally dead — that is a process defect requiring re-design, not a table fix.

**Not a reopening condition:** "the model can do it end-to-end, and it's simpler." Simplicity is already priced into A1's evaluation; it lost on verifiability, and nothing in that trade has changed.

## 7. Architectural design process (how this ADR was produced)

1. **Driver extraction** — from the registry, we ranked the five forces (F1–F5) and fixed the asymmetry: a false `APPROVE` is categorically worse than a false `HOLD`.
2. **Candidate generation** — the plan agent produced four candidates; a fifth (fine-tuned classifier) was dropped early for lack of training data.
3. **Scoring** — each candidate scored against the drivers on a 1–5 scale with the *verifiability* column weighted double (see `docs/architecture/evaluation-table.md`).
4. **Adversarial review** — the human reviewer argued A3's RAG variant and required the extractor to receive table vocabulary as context, which is why A3 survives as a sub-component rather than being discarded.
5. **Invariant derivation** — we wrote the invariants the chosen design *must* satisfy, then asked of each: "what test fails if this is violated?" Any invariant without a failing-test answer was sent back for redesign (this is how INV-001's `COVERAGE_GAP` finding code became mandatory rather than optional).
6. **Reopen conditions** — recorded before implementation, so the decision is falsifiable rather than defended.

## 8. Amendment 1 — 2026-11-14

**Nothing in the decision changed. The wording of one invariant did.**

INV-002 was originally written as *"no output of any component may assert a daily
dose above the applicable maximum"*. A test with a real overdose case showed the
sentence is unimplementable: an overdose case asserts an over-ceiling dose, and it
must, because reporting the breach is the product.

The driver did not move — D1 was always "a wrong APPROVE is unacceptable". The
wording conflated two properties. INV-002 is now stated as two:

1. **Ceiling integrity** — the ceiling in a result equals `max_mg_per_day ×
   band.factor` for the recorded band. A ceiling raised at runtime so a dose passes
   is the violation.
2. **No silent overdose** — an over-ceiling `NormalizedDose` must be accompanied by
   a `DOSE_CEILING` finding. An unreported overdose is the violation.

Also amended at the same time, from the same evidence: a renally cleared drug with
no recorded eGFR no longer has its ceiling compared against a conservative band.
The comparison is skipped and the case is held (`RENAL_DATA_MISSING`). A `BLOCK`
would assert "this dose is too high"; what we know is "we cannot evaluate it".

**Why this is recorded here rather than edited in place:** a reader must be able to
see that we once believed something weaker. An ADR that only contains the final
belief is a press release.
