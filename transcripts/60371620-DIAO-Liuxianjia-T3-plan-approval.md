# Transcript T3 — Plan approval before code

- **Session:** T3 · execution plan, two rejections, approval (D9 gate)
- **Driver:** DIAO Liuxianjia (60371620) · **Annotating:** ⟨M3⟩ BUILD lead, ⟨M5⟩ VERIFY lead
- **Date:** 2026-11-14 · **Baseline:** ADR-001 accepted, `AGENTS.md` present, `src/` empty
- **Sprint:** S0

> **Provenance.** Reconstructed from the S0 build log. The plan text is the plan actually implemented (it matches `AGENTS.md` §5–§7 and the module tree in the repository); the two rejections are the decisions recorded as BUG-0006 and as the "single APPROVE site" constraint in `structural-constraints.md` §5. Condensed where noted.

---

## Setup

> **Human (16:05):** Read `AGENTS.md`, then the blueprint, then ADR-001, then the invariants. Produce an execution plan for the deterministic core only — no extractor model call, no renderer prose. Five sections: traceability, interface contract, scope boundary, testing strategy, steps. Do not write code or tests. Stop for approval.

## Session

### [16:18] Agent — plan v1 (sections 1, 4, 5 only)

> **Traceability.** REQ-I-001 → coverage.py; REQ-I-002 → dose.py; REQ-I-003 → contracts.py.
> **Testing strategy.** One test file `test/test_core.py` covering the happy paths; invariant tests after implementation.
> **Steps.** (1) contracts, (2) rules, (3) adjudicator, (4) tests.

### [16:21] Human intervention — **REJECT** (plan incomplete)

> Three sections of five. No interface contract, no scope boundary, and the testing strategy is "write tests after" — which is the exact inversion `Prompt.md` forbids. A plan missing a section is incomplete; you may not proceed.

**Why.** The missing two sections are where the expensive mistakes live. "Interface contract" is where a model-writable dose field would have appeared; "scope boundary" is where scope creep is caught before it becomes files.

### [16:26] Agent — plan v2, now with a contract change

> **Interface contract.** Add `dose_mg_per_day: float | None` to `ExtractionRecord` so the renderer can display the total daily dose without recomputing it.

### [16:28] Human intervention — **REJECT**

> That field is forbidden by INV-003. The only writer of a dose is `rules.units`. Putting the number in the model-writable contract means the guard now has to police a field we ourselves added — and the next agent will reasonably ask why it exists.

**Why.** This is the failure mode the whole architecture exists to prevent, arriving through the front door: a helpful-sounding convenience that moves an authority field across the seam. It is also BUG-0006's cousin — a boundary crossing that looks like good engineering.

**Instead.** Contract unchanged. `AdjudicationResult` carries `NormalizedDose` objects produced by `rules.dose`; the renderer receives the finished result and restates findings. `dose_mg_per_day` remains in `FORBIDDEN_AUTHORITY_FIELDS`, so a model that emits it is rejected outright.

### [16:34] Agent — plan v3, module layout

> **Module organization.** Single module `src/medcheck/core.py` containing contracts, rules, adjudicator and audit. Simpler to navigate for a small project.

### [16:37] Human intervention — **REDIRECT**

> Simpler for the agent to write, not simpler for us to govern. The blueprint maps one architectural element to exactly one module, and the permission model grants write access per module: a single `core.py` would make "safety-critical path" a synonym for "the whole system", so every PR would need an ADR and the exception would become the rule.

**Instead.** Seven packages as in `AGENTS.md` §5. The structural fitness function `test_no_authority_import` only has teeth because the elements are separable.

### [16:44] Agent — plan v4, testing strategy

> **Testing strategy.** Unit tests per module; invariants covered by the same tests where convenient.

### [16:46] Human intervention — **REJECT**

> "Where convenient" is how an invariant ends up asserted by a test that passes in both worlds. Each invariant needs a test that **fails if the guard is deleted**, and the plan must say how we will check that. Name the mutation.

**Instead.** The plan's §4 became: per-invariant negative tests in `test_invariants.py`, each asserting the *prohibited* outcome (verdict ≠ APPROVE; `CeilingAssertionError`; `AuthorityViolation`), plus a mutation step in the hand-off — delete the guard, observe which test goes red, record it.

### [16:58] Agent — plan v5 (approved form)

> **1. Traceability**
> | REQ/INV | Behaviour | Test |
> |---|---|---|
> | REQ-F-002 | unit normalisation, closed table | `test_units.py::test_mcg_to_mg_conversion`, `::test_unconvertible_unit_raises` |
> | REQ-F-003 | interaction lookup | `test_ddi.py::test_positive_pairs_recall`, `::test_negative_pairs_no_false_positive` |
> | REQ-F-004 | ceiling + renal band | `test_dose.py::test_over_limit_blocked`, `::test_renal_band_selected` |
> | REQ-F-005 | verdict composition | `test_adjudicator.py::test_output_is_byte_identical_over_30_runs` |
> | INV-001 | fail-closed coverage | `test_invariants.py::test_inv001_unknown_drug_is_not_approved`, `::test_inv001_uncovered_pair_holds` |
> | INV-002 | ceiling integrity + no silent overdose | `::test_inv002_dose_ceiling_fuzz`, `::test_inv002_asserted_dose_above_ceiling_rejected` |
> | INV-003 | authority separation | `::test_inv003_model_verdict_rejected` (10 payloads) |
> | INV-005 | traceability | `::test_inv005_every_finding_resolves` |
>
> **2. Interface contract.** No change to `contracts.py`. `Finding(rule_id, code, severity, statement, table_version)` frozen; `AdjudicationResult` frozen; `NormalizedDose(medication, mg_per_day, ceiling_mg_per_day, renal_band)` produced only by `rules.dose`.
>
> **3. Scope boundary.** In: `privacy/`, `rules/`, `adjudicator/`, `audit/`, `renderer/template.py`, `api/cli.py`, `pipeline.py`, `data/rules/*.yaml`. Out: `extractor/llm.py` (needs a key we do not have), semantic evaluation, any web surface. Reason for each exclusion stated.
>
> **4. Testing strategy.** Offline only. One negative test per invariant asserting the prohibited outcome. Mutation check per invariant guard, recorded in `verification-constraints.md` §3. Fixed seed `20261114` for property tests.
>
> **5. Steps.** (1) tables + loader with content-hash version; (2) units; (3) DDI + dose; (4) coverage + verdict + guard; (5) audit; (6) renderer + CLI; (7) tests written before each step's implementation; (8) full suite + gates.

### [17:03] Human — **PLAN APPROVED**

> Approved. Note for the record: steps 3 and 4 must not be merged. Coverage is a separate concept from interaction lookup, and it is the one that decides whether we may approve at all.

---

## Outcome

| Item | Result |
|---|---|
| Artefacts | the seven packages, `data/rules/*.yaml`, `contracts.py`, `pipeline.py` |
| Plan versions | 5; two rejected as incomplete/wrong, one redirected on module layout, one rejected on testing strategy |
| Gate | `PLAN APPROVED` recorded before the first line of code (Phase 3 of `Prompt.md`) |
| What the human caught | a contract change that would have moved an authority field into the model's reach; a module layout that would have made every change safety-critical; a testing strategy with no falsifiable invariant test |
| What the human missed | that the step-4 coverage design had no way to express "pair unassessed" — found in T4, BUG-0002 |
| Annotation count | 4 interventions: 3 REJECT, 1 REDIRECT, 1 APPROVE |
