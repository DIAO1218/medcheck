# MedCheck — Architecture Blueprint

> **Status:** baseline v1.0 · **Revision owner:** architecture review (human-only) · **Read by:** Plan agent on every session, before any other document.
>
> **Location.** Canonical text lives at the repository root, where the required structure (Section 5) places it. A byte-identical mirror sits at `docs/architecture/architecture-blueprint.md`, where D2 requires the artefact; `scripts/sync_blueprint.py --check` fails the build if the two ever drift.
>
> This file is the master constraint document. If an agent instruction, a prompt, or a piece of code conflicts with this blueprint, the blueprint wins and the code is wrong. Amendments require a new ADR under `docs/architecture/adr/` plus human approval (see §10 Change policy).

---

## 1. Scope

MedCheck ingests a free-text clinical case note containing one or more prescribed medications and returns a **reviewable adjudication**: a verdict (`APPROVE` / `HOLD` / `BLOCK`), an ordered list of findings, and a short advisory paragraph for a human reviewer.

**In scope**

| # | Capability | Requirement |
|---|---|---|
| 1 | Extract medications, doses, units, frequency, route, and eGFR from free text | REQ-F-001 |
| 2 | Normalise doses to mg/day with an explicit, closed unit table | REQ-F-002 |
| 3 | Detect drug–drug interactions from a versioned table | REQ-F-003 |
| 4 | Enforce maximum daily dose incl. renal adjustment band | REQ-F-004 |
| 5 | Compose a deterministic verdict with cited findings | REQ-F-005 |
| 6 | Render advisory prose that only restates findings | REQ-F-006 |
| 7 | Append immutable audit records | REQ-F-007 |
| 8 | CLI entry point | REQ-F-008 |

**Out of scope (and deliberately so)**

- Clinical decision support for real patients. This is a teaching artefact; every surface states `NOT FOR CLINICAL USE`.
- Prescribing, dose titration, or any output that could be executed as an order.
- Multi-language intake, handwriting OCR, free-form dose grammars beyond the supported pattern (see `prioritisation.wont`).
- Any verdict produced or modified by a model.

---

## 2. Architectural drivers

Ranked. When two drivers conflict, the lower number wins.

| Rank | Driver | Consequence in the design | Evidence |
|---|---|---|---|
| D1 | **A wrong APPROVE is unacceptable.** The system must be able to fail loudly but must never fail open. | Adjudication is deterministic; unknown coverage escalates to `HOLD` + `COVERAGE_GAP`. | REQ-I-001 |
| D2 | **No number in the output may come from a model.** | Verdict, severity, and dose fields are write-protected outside the deterministic core; a guard rejects model-supplied values. | REQ-I-003, REQ-I-002 |
| D3 | **Every claim must be traceable to a rule.** | Findings carry `rule_id` + `table_version`; a finding that cannot resolve aborts the run. | REQ-I-005 |
| D4 | **Patient identifiers must not leave the process unmasked.** | Masking happens before the model boundary, re-hydration after; logs carry tokens only. | REQ-I-004 |
| D5 | **Humans must be able to review a case in seconds.** | Advisory prose capped at 200 words, ordered by severity, template-bound. | REQ-Q-002 |
| D6 | **The whole pipeline must run offline for CI.** | The deterministic core and all fixtures are offline; only `test/live/` touches a model. | REQ-S-001, CI gate 5 |

---

## 3. System boundaries

```
                     trust boundary ────────────────┐
                                                    │
  case note ──► [privacy.mask] ──► [extractor.llm] ──┼──► (outside process:
     │              │                    │          │     model provider)
     │         (tokens only)             │          │
     │              │                    ▼          │
     │              │            ExtractionRecord   │
     │              │            (schema-checked,   │
     │              │             no verdict field) │
     │              ▼                    │          │
     │        [rules.units] ─────────────┤          │
     │              │                    │          │
     │        [rules.ddi] [rules.dose] ──┤          │
     │              │                    │          │
     │              ▼                    ▼          │
     │        ┌──────────────────────────────┐      │
     └───────►│ adjudicator  (+ guard)       │      │
              │ authoritative: verdict,      │      │
              │ severity, dose ceiling       │      │
              └──────────────┬───────────────┘      │
                             │                      │
                 ┌───────────┼───────────┐          │
                 ▼           ▼           ▼          │
            [renderer]   [audit]     [api.cli]      │
            advisory,    append-     result        │
            template-    only        document      │
            bound        log                        │
```

**What crosses the boundary:** masked case text outbound; a JSON object with no authority fields inbound. Nothing else. Raw identifiers, rule tables, and the verdict never cross.

---

## 4. Components

Each component maps to exactly one module under `src/medcheck/` (see `docs/code-governance/structural-constraints.md`).

| Component | Module | Authority | Model call | Implements |
|---|---|---|---|---|
| `privacy` | `medcheck/privacy` | authoritative | no | REQ-I-004 |
| `extractor` | `medcheck/extractor` | advisory | **yes** | REQ-F-001, REQ-Q-001, REQ-C-001 |
| `rules.units` | `medcheck/rules/units.py` | authoritative | no | REQ-F-002 |
| `rules.ddi` | `medcheck/rules/ddi.py` | authoritative | no | REQ-F-003 |
| `rules.dose` | `medcheck/rules/dose.py` | authoritative | no | REQ-F-004 |
| `adjudicator` | `medcheck/adjudicator` | authoritative | no | REQ-F-005, REQ-I-001/002/003/005 |
| `adjudicator.guard` | `medcheck/adjudicator/guard.py` | authoritative | no | REQ-I-003 |
| `renderer` | `medcheck/renderer` | advisory | optional | REQ-F-006, REQ-Q-001/002 |
| `audit` | `medcheck/audit` | authoritative | no | REQ-F-007 |
| `api.cli` | `medcheck/api/cli.py` | advisory | no | REQ-F-008 |

`medcheck/pipeline.py` is **orchestration, not a component**: it owns the stage order
(§3) and nothing else. It may not contain a rule, a verdict decision, or a privacy
transform — only the wiring, so that reordering the pipeline is a one-file change
that a test can check.

### 4.1 Authority boundaries — advisory vs authoritative

This is the load-bearing table of the whole design.

| Field | Written by | Model may write? | Enforcement |
|---|---|---|---|
| `medications[].name_raw`, `dose_text`, `frequency_text` | `extractor` | **yes** | schema only |
| `medications[].dose_mg_per_day` | `rules.units` | no | recomputed from raw text; extractor value discarded |
| `findings[].rule_id`, `table_version` | `rules.*` / `adjudicator` | no | guarded dataclass, frozen |
| `findings[].severity` | `rules.*` (table lookup) | no | guard rejects any model-supplied severity |
| `verdict` | `adjudicator` | **no** | `AuthorityViolation` before output assembly |
| `advisory_text` | `renderer` | yes (constrained) | conformance test: every statement maps to a finding or template id |
| `audit_record` | `audit` | no | append-only, hash-chained |

**Rule:** no component may read `advisory_text` to decide anything. The advisory is a terminal sink. If an implementation needs the advisory's content to make a decision, the design is wrong and an ADR is required.

### 4.2 Layered context for the AI component

The extractor receives a fixed six-layer context on every turn; assembly, budgeting, and compaction policy are specified in `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md` §5. Summary: identity → standing constraints → retrieved table vocabulary → session history → resumable state → current task, assembled in that priority order under a 3000-token cap with constraint re-injection after any compaction.

---

## 5. Verdict semantics (normative)

Ordered evaluation; the first matching rule wins, and the strongest applicable verdict is the result.

| Order | Condition | Verdict | Finding code |
|---|---|---|---|
| 1 | Any medication or pair absent from the pinned tables | `HOLD` | `COVERAGE_GAP` |
| 2 | Any contraindicated interaction present | `BLOCK` | `DDI_CONTRAINDICATED` |
| 3 | Any daily dose above ceiling (post renal banding) | `BLOCK` | `DOSE_CEILING` |
| 4 | Any major interaction, or eGFR missing where the drug requires it | `HOLD` | `DDI_MAJOR`, `RENAL_DATA_MISSING` |
| 5 | Minor/moderate interaction only | `HOLD` | `DDI_MINOR_MODERATE` |
| 6 | All checks pass with full coverage | `APPROVE` | `ALL_CHECKS_PASSED` |

`APPROVE` is reachable **only** through rule 6, which requires explicit full-coverage confirmation. There is no default-approve path in the code — a new branch that returns `APPROVE` without a coverage proof is a defect by definition (REQ-I-001).

---

## 6. Agent workflow (the supervised pipeline)

| Stage | Agent role | Output | Human gate |
|---|---|---|---|
| S1 Requirements classification | `plan-agent` (read-only on src) | requirement diff proposal | human approves registry change |
| S2 Candidate generation + evaluation | `plan-agent` | ≥2 candidate architectures + evaluation table | human picks, ADR recorded |
| S3 Plan authoring | `plan-agent` | execution plan: traceability, interface contract, scope boundary, test strategy | **hard stop — no code until approved** |
| S4 Test authoring | `build-agent` (test/ writable) | failing tests referencing requirement ids | **test approval gate** |
| S5 Implementation | `build-agent` (src/ writable, safety paths need ADR) | code + passing tests | review memo per PR |
| S6 Verification | `verify-agent` (read-only everywhere) | three-tier report + verdict | human signs review memo |
| S7 Revision | any | ADR amendment + changed constraints | human approves amendment |

Every stage's transcript is captured under `transcripts/` with the interventions marked (D5).

---

## 7. Permissions

Deny-by-default. Full matrix in `docs/architecture/permission-model.md`; machine-readable form in `.opencode/permissions.jsonc`. Three roles: `plan-agent` (reads everything except `data/rules` history, writes `docs/` only), `build-agent` (writes `src/`, `test/`, `prompts/`; **cannot** write `.opencode/`, `.agent/`, `AGENTS.md`), `verify-agent` (writes only `docs/review-memo.md` and CI reports). No role may write `.agent/rules.md`, `AGENTS.md`, or `docs/architecture/adr/` — those are human-only.

---

## 8. Verification strategy

Three tiers, all enforced by CI gates (`.github/workflows/ci.yml`):

1. **Structural** — import graph matches the component table; no module imports another module's internals; architectural fitness functions (e.g. "`renderer` does not import `adjudicator` internals", "`extractor` never imports `audit`"); permission manifest matches the blueprint.
2. **Regression** — every prior sprint's suite runs; any regression blocks.
3. **Behavioral** — semantic thresholds (faithfulness ≥ 0.90, relevance ≥ 0.85) on the frozen evaluation set; invariant suites must report exactly zero violations.

Each fit criterion in the registry has at least one test; each invariant has at least one test that fails when the invariant is violated (see `docs/code-governance/verification-constraints.md`).

---

## 9. Observability

| Signal | Where | Alert condition |
|---|---|---|
| `verdict` distribution | audit log | `APPROVE` share jumps > 15 points week-over-week (sign of a default-approve bug) |
| `COVERAGE_GAP` rate | audit log | > 20% of cases (table coverage is drifting from real inputs) |
| invariant violation counter | `test/offline/test_invariants.py` + CI | **any non-zero value is a release blocker** |
| `AuthorityViolation` count | runtime log | any occurrence is a P1 bug with an ADR follow-up |
| p95 adjudication latency | benchmark test | > 50 ms (REQ-P-001) |
| semantic scores | `scripts/eval_replay.py` | below thresholds blocks prompt/model changes |
| unmasked identifier hits | `test/offline/test_privacy.py` | any hit is a release blocker (REQ-I-004) |

---

## 10. Change policy

| Change | Requires |
|---|---|
| Any file under `src/medcheck/{adjudicator,rules,privacy,audit}` (safety-critical) | new/amended ADR + human reviewer + full invariant suite |
| Per-field change to the extractor contract | ADR amendment (contract change ripples into `rules.units`) |
| Adding a dependency | allowlist update reviewed by human (REQ-S-002) |
| Prompt or model change under `prompts/` | semantic evaluation gate + AI-use log update |
| Any doc under `docs/architecture/` | human-only edit; agents propose, humans commit |
| `AGENTS.md`, `.agent/rules.md`, `.opencode/rules.md` | human-only, never agent-written |
| Relaxing any invariant | **not permitted**. Invariants change only by re-deriving them from a driver change, with an ADR that states which driver moved. |

Rules must be refreshed within one sprint of a requirement change (`.agent/rules.md`, context-freshness clause). Stale rules are treated as a defect, tracked in `docs/debt-register.md`.
