# Evaluation Logbook

The accumulated evidence behind architecture and process decisions. Every entry is dated, has a measurement or an observation, and ends in a **consequence** — a change to an artefact. An entry with no consequence is a diary, not a logbook.

Format: `E-nn · date · area · evidence → consequence`.

---

## Sprint 0 — set-up and first decisions

**E-01 · 2026-11-14 · requirements · schema gate caught a non-falsifiable criterion**
The first registry draft failed its own gate: `REQ-P-001`'s fit criterion was `"p95 <= 50 ms."` — 14 characters, rejected by the schema's `minLength: 20`. On inspection the problem was not length but content: the criterion named a number without naming *what was measured*, *on what corpus*, or *where the result is reported*.
→ Rewritten to name the function, the corpus (1000 warm-table cases), the runner, and the owning test. **Consequence:** the gate stayed at `minLength: 20` but the team adopted the rule that a fit criterion must contain a quantity *and* a measurement site; recorded in `verification-constraints.md`.

**E-02 · 2026-11-14 · architecture · candidate scoring was re-weighted after adversarial review**
First scoring pass weighted build effort ×3 ("we have one semester"). A4 still won, but by a margin thin enough that a bad week would have flipped it.
→ Effort dropped to ×1, provability raised to ×3, offline-CI to ×2. Rationale recorded in `evaluation-table.md` §1: effort is recoverable, provability is not. **Consequence:** the sensitivity table now exists, so a future team can see which weighting changes the winner and argue about the weight instead of the winner.

**E-03 · 2026-11-14 · architecture · A3 (RAG decides) was not discarded outright**
Review argued that rejecting retrieval entirely would hurt drug-name canonicalisation. Re-ran the comparison separating "RAG as decision path" from "RAG as perception aid".
→ A3 kept as a **sub-component** (table vocabulary injected as context layer L3), rejected as a decision path. **Consequence:** ADR-001 §3 records the split, and `option-ledger.md` O-3 carries the trigger for revisiting.

**E-04 · 2026-11-14 · invariants · one invariant lacked a failing test, so it was rewritten**
First draft of INV-001 said "unknown drugs must be handled safely." No test can fail on that — "safely" is not observable.
→ Rewritten to a prohibited outcome with a named finding code: verdict must not be `APPROVE`; must carry `COVERAGE_GAP`. **Consequence:** the rule "an invariant without a failing-test answer goes back for redesign" was added to the ADR's design process (§7 step 5).

**E-05 · 2026-11-14 · governance · permission model has a single point of failure**
While writing `.opencode/permissions.jsonc` we noticed the file is the only barrier between `build-agent` and the constraints it is judged by.
→ Added four defences: human-only surfaces declared in the blueprint (§7), a CI sync check between matrix and JSONC, a 12-path denial test, and a mandatory review-memo line. **Consequence:** `risk-list.md` R-06 opened with the trigger "any PR touching a human-only surface".

---

**E-06 · 2026-11-14 · verification · two of five invariant guards are load-bearing, three are unproven**
Mutation check: deleting the unknown-drug branch in `coverage.assess` failed `test_inv001_unknown_drug_is_not_approved` (1 failure); replacing the authority-field check in `_assert_no_authority` with an empty set failed all 10 parametrisations of `test_inv003_model_verdict_rejected`. INV-002, INV-004 and INV-005 were asserted by tests but not mutation-checked in this pass.
→ Recorded the two results in `verification-constraints.md` §3 and opened **DEBT-09** for the unproven three rather than claiming five.
**Consequence:** the claim in the report is now "two guards proven load-bearing, three pending", which is smaller and true.

**E-07 · 2026-11-14 · performance · the deterministic core is three orders of magnitude inside its budget**
`process_case` over 500 warm cases on the development machine: p50 0.06 ms, p95 0.07 ms, against the 50 ms ceiling in REQ-P-001.
→ No optimisation work authorised. The budget stays as written: it is a regression tripwire, not a target to approach.
**Consequence:** runtime pressure on the design is now known to be zero, which removes "performance" as a justification for any future shortcut through the deterministic core.

**E-08 · 2026-11-14 · evaluation · the promised corpus was 100 cases; we closed at 25**
T1 wrote "faithfulness and relevance on 100 frozen cases". S0 closed with 25 (6 APPROVE, 14 HOLD, 5 BLOCK). The gate could not tell the difference, because it evaluates scores, not corpus size.
→ `REQ-Q-001` amended to name the 25-case set (registry revision 1 → 2), DEBT-02 moved to repaid, and the residual risk that 25 self-written cases under-represent the APPROVE family opened as DEBT-11.
**Consequence:** a threshold without a corpus size is a threshold that can be met by shrinking the corpus. The schema now has nowhere to record corpus size — opening that gap as DEBT-12 rather than adding a field mid-sprint.

**E-09 · 2026-11-14 · privacy · the evaluation set violated our own security rule**
Growing the set to 25 added a fixture carrying an HKID-shaped string. REQ-S-001's gate failed on it within the same run (BUG-0007).
→ Fixture deleted; PHI coverage moved in-process to `test_privacy.py`, where the note exists only in memory; replacement fixture keeps the set at 25.
**Consequence:** "synthetic" was re-read as a property of the *repository*, not of the string — a fake identifier is still an identifier-shaped artefact in a diff.

## Sprint 1 — build (to be filled at sprint close)
| Planned measurement | Purpose | Threshold |
|---|---|---|
| Unit-conversion fixture pass rate | prove REQ-F-002 before touching dose logic | 60/60 |
| DDI recall / false-positive count | prove REQ-F-003 | 40/40, 0 FP |
| Invariant suite violation count | prove INV-001…005 are wired, not aspirational | exactly 0 |
| Mutation check: delete the `COVERAGE_GAP` branch, does a test fail? | prove the negative test is load-bearing | test must fail |
| `adjudicate()` p95 | REQ-P-001 headroom | ≤ 50 ms |
| Extraction field accuracy (heuristic baseline) | establish the floor before any model work | report only |

**Entry template**

```
**E-nn · <date> · <area> · <one-line finding>**
<what was measured or observed, with numbers>
→ <what changed in which artefact>
**Consequence:** <the durable effect — a rule, a test, a threshold, a risk trigger>
```

Rule for this file: an entry that reports a success with no measurement is deleted at sprint review. We log evidence, not morale.
