# Compliance matrix — CS5351 project requirement sheet

Every line of `CS5351-2026-2027-project.pdf` mapped to the artefact that satisfies it, with an honest status. Three statuses only: **met**, **met with a stated deviation**, **open** (cannot be closed by the artefacts alone).

Audited 2026-11-14 against registry revision 2 and tag `s0-baseline`.

---

## Submission model

| Requirement | Artefact | Status |
|---|---|---|
| One repository | `MedCheck/` (git initialised, 8 commits, tag `s0-baseline`) | met locally; **remote pending** (see §Open) |
| Five annotated agent-session transcripts | `transcripts/T1…T5` | met, with provenance caveat |
| One process report | `Report.md` | met |
| AI-use log mandatory and up to date | `docs/ai-use-log.yaml` (5 entries) | met |

## D1 — Requirements (machine-readable, `./docs/req/`)

| Requirement | Artefact | Status |
|---|---|---|
| Machine-readable PRD, YAML | `docs/req/requirements.yaml` → `product_context` (vision, users, in/out of scope, success metrics, non-goals) | met — PRD and registry are two blocks of one file, deliberately |
| Consolidated registry, YAML | same file → `requirements` (25 entries) | met |
| Every entry: ID, type, statement, machine-checkable fit criterion, priority | enforced by `req-schema.json` (`required` + `pattern` + `minLength`) and `scripts/validate_requirements.py` | met, gate-verified |
| Types cover functional, invariants, quality, performance, cost, governance, security | 8 F / 5 I / 2 Q / 2 P / 1 C / 2 S / 5 G | met |
| Invariants are zero-tolerance | `zero_tolerance: true` enforced conditionally by schema; cross-field check rejects invariants without it | met |
| NFRs as metric + threshold + verification | required fields for `quality`/`performance`/`cost` types (schema `allOf`) | met |
| MoSCoW + explicit tradeoff | `prioritisation.framework`, `tradeoff` (40+ chars enforced) | met |
| Requirements discovered from an existing system, linked to source | `REQ-I-001` ← `SRC-ANALYSIS-01` → `docs/bug-diary.md#BUG-0002` | met |
| `req-schema.json` used by CI to validate the registry | `.github/workflows/ci.yml` job `schema-gate` → `scripts/validate_requirements.py` | met |

*Deviation:* the sheet's prose says "both in YAML" but names the schema `.json`; we follow the filename, since a JSON Schema in YAML would not be usable by standard validators.

## D2 — Architecture artefacts (`./docs/architecture/`)

| # | Artefact | File | Status |
|---|---|---|---|
| 1 | Blueprint: scope, drivers, boundaries, components, authority boundaries, agent workflow, permissions, verification strategy, observability, change policy | `architecture-blueprint.md` (+ byte-identical mirror in `docs/architecture/`) | met — see deviation below |
| 2 | ADR: chosen architecture, alternatives, rationale, consequences, reopen conditions, design process | `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md` §2–§7 | met |
| 2 | Layered context for the AI component (six layers) | ADR §5 (L1 identity → L6 task) | met |
| 2 | Assembly pipeline: dedupe, prioritise, budget, compact, assemble | ADR §5, implemented in `extractor/context.py` | met |
| 2 | Token-budget cap + compaction threshold | 3000 / 2400 (80%), ADR §5 + `test_context_assembly.py` | met |
| 2 | Re-injection policy after compaction | L2 re-injected verbatim before L6, asserted by `test_compaction_reinjects_constraints` | met |
| 3 | Invariant register: statement, source req, enforcing component, verification, operational fallback | `docs/architecture/invariants.md` (5 rows, all five columns) | met |
| 4 | Trace matrix: requirement → component → test → runtime monitor | `docs/architecture/trace-matrix.md` (25 rows) | met |
| 5 | Memory/state design: survival across sessions/interruptions/versions, write + retrieval policy, ownership, retention, privacy | `docs/architecture/memory-design.md` §1–§6 | met |
| 6 | Permission model: file-level rights per role, default deny, explicit whitelist | `docs/architecture/permission-model.md` + `.opencode/permissions.jsonc` | met |
| 7 | Runtime policy catalog: degraded/failure paths | `docs/architecture/runtime-policy-catalog.md` (P-01…P-22) | met |
| 8 | Candidate evaluation table | `docs/architecture/evaluation-table.md` (5 candidates, weights, sensitivity) | met |
| 9 | Evaluation logbook (optional) | `docs/architecture/evaluation-logbook.md` (E-01…E-09) | met |
| 10 | Risk list (optional) | `docs/architecture/risk-list.md` (R-01…R-12, each with a review trigger) | met |
| 11 | Option ledger (optional) | `docs/architecture/option-ledger.md` (O-1…O-12, each with a revisit trigger) | met |

*Deviation:* D2 requires every artefact in `./docs/architecture/`, while the required repository structure (§5) puts `architecture-blueprint.md` at the root. Both are satisfied: the root file is canonical and `docs/architecture/architecture-blueprint.md` is a byte-identical mirror, with `scripts/sync_blueprint.py --check` and `test_blueprint_exists_in_both_required_locations` failing the build if they drift. Choosing one location would have broken the other requirement silently.

## D3 — Coding governance

| Requirement | Artefact | Status |
|---|---|---|
| `AGENTS.md` at root: build target, reading order, code baseline, readable/modifiable/frozen, module organisation, integration contracts, verification requirements | `AGENTS.md` §1–§8 | met |
| `structural-constraints.md`: one element ↔ one module; extend never replace; every module/function cites its ADR and invariant; authority boundaries | `docs/code-governance/structural-constraints.md` §1–§7; modules carry `Decision: ADR-001 … Invariants: …` headers | met |
| `mcp-tool-manifest.md`: tools + which roles may call them | `docs/code-governance/mcp-tool-manifest.md` (4 tables + prohibitions) | met |
| `.opencode/permissions.jsonc`: machine-readable permissions, guard rules, enforcement | `.opencode/permissions.jsonc` (roles, guards, shell + egress allowlists) | met |
| `.opencode/rules.md`: always-on behavioural rules, human-only | `.opencode/rules.md` (marked human-only in permission model §5) | met |
| `.agent/rules.md`: covenant — abstraction limits, dependency constraints, test independence (≥1 negative test per feature), safety-critical change needs ADR + human approval, context freshness (≤1 sprint) | `.agent/rules.md` §1–§6 | met |

## D4 — Verification governance

| Requirement | Artefact | Status |
|---|---|---|
| Every fit criterion has ≥1 test | `docs/architecture/trace-matrix.md`; enforced by `test_every_requirement_is_traced` | met |
| Every invariant has a test that fails when violated | `test_invariants.py` — mutation-checked for INV-001/003, others asserted | partially met — 3 of 5 unproven (DEBT-09) |
| Every test references the requirement/invariant it verifies | all 136 test functions carry an id; enforced by `test_every_test_declares_its_requirement` | met |
| Every round runs all prior suites, zero regressions | CI gate 5 runs `test/offline` in full | met |
| Three tiers: structural, regression, behavioural | `verification-constraints.md` §2 + gate map | met |
| `review-memo.md`: per PR, spec/architecture/quality/operational, security + efficiency, verdict | `docs/review-memo.md` — PR #0 (CHANGES REQUIRED) and #1 (APPROVE) | met (2 memos, 2 PRs) |
| `debt-register.md`: all eight AI-era categories | `docs/debt-register.md` — prompt rot (06), hallucinated dependency (13), untouchable code (05,10), hidden dependency (04), agent-induced bloat (08), evaluation debt (01,11,12), guardrail debt (03,09), human/cognitive debt (07) | met |
| `bug-diary.md`: symptom, reproduction, classification, root cause, fix, invariant gap | `docs/bug-diary.md` — 7 entries, all six fields + gap | met |

## D5 — Agent session transcripts

| Requirement | Artefact | Status |
|---|---|---|
| One full raw transcript building the implementation | `transcripts/…-T4-build-verify.md` | met, reconstructed |
| Five annotated transcripts | T1–T5 | met |
| Marked interventions with a rationale each | 30 markers (8 REJECT, 9 REDIRECT, 4 CORRECT, 3 INTERRUPT, 6 APPROVE), each with **Why** and **Instead** | met |
| Collectively show: requirements classification, candidate generation + evaluation, plan approval before code, build, verification compliance, architecture revision from test evidence | T1, T2, T3, T4, T4+§7, T5 respectively | met |

*Deviation:* the files are **reconstructions** from the build log — agent output verbatim, human turns condensed from recorded decisions — and each says so in its header. The specification asks for recorded sessions; the team must certify or re-record (§Open).

## D6 — Report

| Requirement | Artefact | Status |
|---|---|---|
| Single markdown file | `Report.md` | met |
| All students' names and student numbers | §1 mapping table | **open** — `⟨M1⟩`–`⟨M6⟩` placeholders |
| Whole team's relative contribution | §1 hours table + weight formula + worked example | structure met; hours **open** |
| ≤ 10,000 words excluding diagrams | 9,279 words | met |
| > 15 pages at Point 12, single spacing | ≈18 pages at ~500 words/page incl. 4 appendices and 12 tables | met (estimated; confirm in your PDF export) |
| Team's SE process and how it is optimised | §3, §8 | met |
| Self-reflection 300–500 words per student, with name and ID | §13, six sections at 314–384 words | length met; **voice + signature open** |
| Process quality evidence: requirement volatility, defect trends, ambiguity resolution | §9.1, §9.2, §9.3 | met |
| Artefacts co-evolving on change | §10 (six-row propagation table + enforcing mechanism) | met |
| What human oversight caught that the agent did not | §11, three specific cases + what machines caught | met |

## D7 — Repository and CI

| Requirement | Artefact | Status |
|---|---|---|
| Source, tests, CI/CD with blocking gates, branch protection, meaningful history | `src/`, `test/`, `.github/workflows/ci.yml`, 8 commits + tag | history met; **branch protection open** (GitHub setting, not a file) |
| README states the design of the blocking gates | `README.md` §"The six blocking gates" + rationale paragraph | met |
| Six blocking gates | `ci.yml`: test-approval, static-analysis, schema-gate, semantic-evaluation, regression, ai-use-log, plus `all-gates` aggregator | met |
| Each gate self-tested | `test_gates_selftest.py`, `test_requirements_schema.py`, `test_permissions.py`, `test_semantic_gate.py` (REQ-G-005) | met |

## D8 — Source and tests

| Requirement | Artefact | Status |
|---|---|---|
| `src/` and `test/` with full source and cases | `src/medcheck/` (7 packages + 2 modules), `test/offline` (195), `test/live` (3) | met |
| Module names match architectural elements | `structural-constraints.md` §1 table ↔ directory listing; enforced by `test_component_module_mapping` | met |
| Test layout separates deterministic offline from live | `test/offline/`, `test/live/` with `pytestmark = live` | met |

## D9 — Static prompt

| Requirement | Artefact | Status |
|---|---|---|
| Single static file `./Prompt.md` | `Prompt.md` | met |
| Instructs: produce execution plan (traceability, interface contract, scope boundaries, testing strategy, steps) | Phase 1, five-section table | met |
| Stops for human approval before generating code | Phase 1 hard stop on `PLAN APPROVED`; "silence is not approval" | met |
| Does not run the agent unattended to completion | Phase 5 hand-off; standing prohibitions | met |

## Submission format and required structure

| Requirement | Status |
|---|---|
| Zip with the §5 directory structure | met (`CS5351-MedCheck.zip`); regenerate after any edit |
| README: purpose + architecture in a few paragraphs | met (§ Purpose and architecture, three paragraphs) |
| README: organisation of project files | met (annotated tree) |
| README: how to run offline, live, full suite | met (three commands + exit codes) |
| README: GitHub repo that contains the real project | **open** — placeholder URL |

Structure check: every path in §5 exists, plus a mirror of the blueprint, `docs/test-approvals.yaml`, `SUBMISSION-CHECKLIST.md`, `docs/compliance-matrix.md`, `data/rules/`, `scripts/`.

---

## Open items (cannot be closed by editing artefacts)

| # | Item | Who | Why it cannot be automated |
|---|---|---|---|
| 1 | Six names + student numbers, per-sprint hours, weights | team | hours are not recoverable from the repository; inventing them corrupts the one measure the sheet asks for |
| 2 | Six reflections rewritten in each member's own voice + signed | team | a reflection written by an agent is not a reflection |
| 3 | Transcripts certified or re-recorded | team | they are reconstructions; certification is a statement only the team can make |
| 4 | GitHub remote + branch protection (require `ci`, require review + ADR on safety paths) | team | repository settings, not files |
| 5 | Live extractor accuracy (`prompts/*.yaml: live_accuracy`) | team | needs an API key and real notes |
| 6 | Mutation check for INV-002/004/005 | team | 1 hour of work, closes DEBT-09 |

## Deviations, stated rather than hidden

1. **Blueprint in two locations** — resolved by mirroring with a build-enforced equality check, because D2 and §5 disagree.
2. **PRD and registry in one file** — two YAML documents that must agree are two documents that will drift; the schema validates both blocks.
3. **Transcripts are reconstructions** — stated in five headers, the transcripts README, the review memo and Report §6.3.
4. **`req-schema.json` is JSON** — following the sheet's own filename over its prose.
5. **Hours and reflections are blank/placeholder** — a fabricated number is worse than an empty cell, and this project argues that in three places.
