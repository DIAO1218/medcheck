# MedCheck

中文版: [README.md](README.md) · Chinese companion docs: [docs/zh/README.md](docs/zh/README.md)

**Medication interaction and dose-ceiling adjudication with a deterministic safety core.**
*CS5351 Agentic Software Engineering Project — NOT FOR CLINICAL USE.*

MedCheck reads a free-text clinical case note and returns a reviewable adjudication: a verdict (`APPROVE` / `HOLD` / `BLOCK`), an ordered list of cited findings, and a short advisory paragraph. The product is a teaching artefact, not clinical software; every output says so.

## Purpose and architecture, in three paragraphs

**The seam.** A language model reads the note; deterministic code decides. The model maps prose to a schema-checked `ExtractionRecord` and never sees the rule tables, never emits a verdict, never computes a dose. Everything that can be wrong in a way that matters — unit normalisation, interaction lookup, dose ceilings, coverage accounting, verdict composition — is a table lookup or a comparison, which means the same input and the same table version produce byte-identical output. The model reappears at the exit as a constrained paraphraser, and nothing downstream reads its output.

**Why the seam is there.** A confident wrong `APPROVE` is the failure that matters; a spurious `HOLD` costs a reviewer a minute. An end-to-end model verdict cannot be proven offline, cannot be audited to a rule, and cannot be regression-tested without the model itself — so the three properties the course requires (verifiability, traceability, reproducibility) all become aspirations. The seam is enforced three times: the extraction contract has no field for a verdict, only one module may assign `Verdict.APPROVE`, and an architectural fitness function fails the build if the perception layer even imports the adjudicator. See `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md`.

**Fail-closed, visibly.** If a drug or a drug pair is not covered by the pinned tables — including pairs the table explicitly declares *unassessed* — the verdict cannot be `APPROVE`. It becomes `HOLD` with a `COVERAGE_GAP` finding, and the gap rate is a monitored signal: above 20%, the answer is a coverage sprint, never a looser verdict policy. The design preference is a queue of holds a human reads over a stream of approvals nobody checks.

## Project layout

```
.
├── README.md                     this file
├── AGENTS.md                     coding-agent entry point: reading order, boundaries, hard stops
├── architecture-blueprint.md     master constraint document (D2.1)
├── Prompt.md                     static startup prompt, five gated phases (D9)
├── Report.md                     process report + reflections (D6, 8,560 words)
├── SUBMISSION-CHECKLIST.md       what only the team can do before zipping
├── docs/compliance-matrix.md     every requirement-sheet clause → artefact → status
├── docs/
│   ├── req/
│   │   ├── requirements.yaml     25 requirements, 5 invariants, PRD block + MoSCoW (D1)
│   │   └── req-schema.json       CI schema for the registry (D1)
│   ├── architecture/             ADR, invariants, trace matrix, memory, permission model,
│   │                             runtime policy catalog, evaluation table + logbook,
│   │                             risk list, option ledger (D2)
│   ├── code-governance/          structural + verification constraints, MCP tool manifest (D3, D4)
│   ├── compliance-matrix.md      clause-by-clause audit against the requirement sheet
│   ├── ai-use-log.yaml           mandatory; gate 6 blocks an unlogged code/prompt change
│   ├── test-approvals.yaml       approval ledger for gate 1 / gate 6
│   ├── review-memo.md            per-PR review record + verdict (D4)
│   ├── debt-register.md          debt in AI-era categories (D4)
│   └── bug-diary.md              six real defects with the invariant gap each exposed (D4)
├── .opencode/                    permissions.jsonc (machine-readable) + rules.md (human-only)
├── .agent/rules.md               project covenant (human-only)
├── .github/workflows/ci.yml      six blocking gates (D7)
├── prompts/                      prompt_v1.0.yaml, prompt_v1.1.yaml
├── src/medcheck/
│   ├── contracts.py              frozen boundary types
│   ├── privacy/                  mask / unmask / scrub        (INV-004)
│   ├── extractor/                heuristic, llm, context      (perception)
│   ├── rules/                    units, ddi, dose, loader      (authority)
│   ├── adjudicator/              verdict, coverage, guard      (authority)
│   ├── renderer/                 template                      (advisory sink)
│   ├── audit/                    append-only hash chain        (REQ-F-007)
│   ├── api/                      cli, permissions
│   └── pipeline.py               the only place stages are wired
├── data/rules/                   units.yaml, ddi.yaml, dose.yaml (human-writable only)
├── scripts/                      validate_requirements, check_ai_use_log,
│                                 check_test_approval, check_permissions_sync,
│                                 eval_replay, build_ddi_fixtures
├── test/offline/                 195 deterministic tests, no network, no model
├── test/live/                    model-dependent, marked `live`, never in CI gate 5
└── transcripts/                  five annotated agent sessions (D5) — protocol only, see README
```

## Running the tests

```bash
pip install -e ".[dev]"          # pyyaml + pytest + jsonschema

# offline suite: deterministic, no model, no network (this is what CI gate 5 runs)
python -m pytest test/offline -q

# live suite: requires a model endpoint; marked `live`, skipped when unconfigured
export MEDCHECK_LLM_BASE_URL="https://<gateway>/v1"
export MEDCHECK_LLM_API_KEY="<key>"
python -m pytest test/live -q

# everything (live tests self-skip without credentials)
python -m pytest -q
```

Try the product:

```bash
python -m medcheck.api.cli --case test/fixtures/cases/block_ddi.json --advisory
python -m medcheck.api.cli --case test/fixtures/cases/ok_single_drug.json --audit data/audit/audit.jsonl
```

Exit codes: `0` adjudicated · `2` malformed input · `3` invariant abort / invalid table · `4` audit unavailable (result deliberately withheld).

## The six blocking gates

| # | Gate | Script / job | Blocks when |
|---|---|---|---|
| 1 | Test approval | `scripts/check_test_approval.py` | a touched module has no approved test record (or a safety-critical module has no ADR) |
| 2 | Static analysis | `ruff`, `compileall`, structural tests, permission sync | lint/compile/import-boundary/permission drift |
| 3 | Schema | `scripts/validate_requirements.py` | the registry violates its JSON schema or a cross-field rule |
| 4 | Semantic evaluation | `scripts/eval_replay.py` | faithfulness < 0.90 or relevance < 0.85 on the frozen set |
| 5 | Regression | `pytest test/offline` | any prior test fails, or an invariant suite reports a violation |
| 6 | AI-use log | `scripts/check_ai_use_log.py` | `src/` or `prompts/` changed without `docs/ai-use-log.yaml` |

**Branch protection:** `ci` must pass; changes under `src/medcheck/{adjudicator,rules,privacy,audit}`, `data/rules/`, `.opencode/`, or `.agent/` additionally require a human review with an ADR id in the PR body. Gate 1 was red until the S0 close review, because the baseline was written in one pass and no prior approval existed; `docs/test-approvals.yaml` now records that approval retroactively, and the review memo says why that is visible rather than tidied away.

## Where to look first

| If you want to… | Read |
|---|---|
| check the submission against the requirement sheet | `docs/compliance-matrix.md` (clause → artefact → status) |
| know what only the team can do | `SUBMISSION-CHECKLIST.md` |
| see the one decision everything else follows from | `docs/architecture/adr/001-…md` |
| see what broke and what found it | `docs/bug-diary.md` (7 defects, 0 found by reading code) |
| see the agent being supervised | `transcripts/` (30 marked interventions) |

## Status, honestly

| Deliverable | State |
|---|---|
| D1 requirements + schema | complete, gate-verified |
| D2 architecture artefacts (11) | complete (blueprint at root per the required structure) |
| D3 coding governance | complete |
| D4 verification governance | complete; review memo #0 = CHANGES REQUIRED |
| D7 repo + CI gates | complete; gates self-tested |
| D8 source + tests | deterministic core complete, 195 offline tests green; live extractor wired but unmeasured |
| D5 five annotated transcripts | recorded T1–T5, 30 annotated interventions; provenance stated in each file |
| D6 report | complete in content (8,560 words, ~17 pages at Point 12); names, hours and personal reflections are the team's to fill (`⟨M1⟩`–`⟨M6⟩`) — see `SUBMISSION-CHECKLIST.md` §2 |

The transcripts are reconstructed from the S0 build log with agent output quoted verbatim and human turns condensed from recorded decisions. Each file says so at the top; the team must certify or re-record them (`transcripts/README.md`). A reader should treat the green suite as evidence about the deterministic core, and the transcripts as evidence about supervision only once certified.

## Design decisions worth arguing with

- [ADR-001](docs/architecture/adr/001-deterministic-core-model-at-the-edges.md) — the seam, and the five conditions that would reopen it.
- [Evaluation table](docs/architecture/evaluation-table.md) — why the chosen architecture wins under every weighting that keeps provability as a criterion, and the one weighting where it loses.
- [Option ledger](docs/architecture/option-ledger.md) — twelve rejected options with the trigger that brings each back.
- [Bug diary](docs/bug-diary.md) — six defects found by artefacts disagreeing, not by reading code.

---

**Repository:** `<https://github.com/<org>/medcheck>` — replace with the real GitHub URL before submission (required by the submission format).
