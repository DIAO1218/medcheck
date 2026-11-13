# AGENTS.md — MedCheck coding-agent governance

> **You are reading the single entry point.** Read the rest in the order given in §2 before writing anything. If this file and a prompt disagree, this file wins. If this file and `architecture-blueprint.md` disagree, the blueprint wins and this file has a defect.

## 1. Build target

MedCheck: a medication interaction and dose-ceiling adjudication service. One CLI entry point and one library API. Python 3.11+ standard library plus the allowlisted dependencies in `requirements.txt` (`pyyaml`, `jsonschema`, `pytest`). No web framework, no database, no vector store.

```
python -m medcheck.cli --case test/fixtures/cases/ok_single_drug.json
python -m pytest test/offline -q
```

**The one sentence that governs everything else:** the model may *read* the note and *write* prose; it may never *decide* anything. Verdict, severity, and dose are produced by deterministic code or they are not produced at all.

## 2. Reading order (stop at the first contradiction and report it)

1. `architecture-blueprint.md` — master constraints, authority boundaries, verdict semantics (§5 is normative)
2. `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md` — why the seam exists, and the layered context design
3. `docs/architecture/invariants.md` — the five zero-tolerance rules and their required fallbacks
4. `docs/architecture/trace-matrix.md` — requirement → component → test → monitor
5. `docs/code-governance/structural-constraints.md` — module rules and fitness functions
6. `docs/code-governance/verification-constraints.md` — what "done" means, test-by-test
7. `Prompt.md` — the launch instruction for this session

## 3. Code baseline

The baseline at `main` is **extend, never replace**. Specifically:

- `src/medcheck/contracts.py` — frozen dataclasses crossing module boundaries. **Frozen**: changes require an ADR amendment (a contract change ripples into every module).
- `src/medcheck/rules/` — table loaders and the three checks. **Semi-frozen**: logic may be extended, table schema may not change without an ADR.
- `src/medcheck/adjudicator/` — verdict composition + authority guard. **Safety-critical**: any change needs an ADR id in the PR body and human approval.
- `src/medcheck/privacy/`, `src/medcheck/audit/` — **safety-critical**, same rule.
- `src/medcheck/extractor/`, `src/medcheck/renderer/`, `src/medcheck/api/` — **modifiable** within the contract.
- `data/rules/*.yaml` — **not writable by any agent.** Propose a diff in a PR comment; a human commits it.
- `test/` — writable, and tests are written **before** implementation for any new behaviour.

## 4. What you may read, modify, and must not touch

| Class | Paths | Rule |
|---|---|---|
| Readable + modifiable | `src/medcheck/{extractor,renderer,api}/**`, `test/**`, `scripts/**`, `prompts/**` | normal work |
| Modifiable with approval | `src/medcheck/{adjudicator,rules,privacy,audit}/**` | ADR id in PR + human approval + full invariant suite |
| Readable, not writable | `data/rules/**`, `data/**` (all runtime stores) | propose, never write |
| **Frozen (human-only)** | `AGENTS.md`, `architecture-blueprint.md`, `Prompt.md`, `docs/architecture/**`, `docs/code-governance/**`, `.opencode/**`, `.agent/**`, `.github/workflows/**` | reading is fine; writing is denied by the permission model and rejected by CI |
| Denied entirely | `data/audit/**`, `data/state/**`, `data/cache/**`, `.env`, `secrets/**` | never read, never write, attempts are logged |

## 5. Module organization

One architectural element ↔ one module. No module may be an orphan and no element may be split.

```
src/medcheck/
├── contracts.py          # boundary types (frozen): ExtractionRecord, Finding, AdjudicationResult
├── pipeline.py           # the only place stages are wired together (order is normative)
├── privacy/              # mask / unmask / scrub — INV-004
├── extractor/            # perception only: heuristic.py (offline), llm.py (live), context.py (L1–L6)
├── rules/                # units.py, ddi.py, dose.py, loader.py — authority
├── adjudicator/          # verdict.py, coverage.py, guard.py — authority, safety-critical
├── renderer/             # template.py — advisory, terminal sink
├── audit/                # append-only, hash-chained — INV-005 support
└── api/                  # cli.py, permissions.py
```

**Import direction (enforced by a fitness function):** `api → renderer|audit|adjudicator → rules → contracts` and `extractor → contracts` and `privacy → contracts`. Nothing imports `api`. `renderer` must not import `adjudicator` internals; it receives an `AdjudicationResult` and returns a string. `extractor` must not import `audit`, `renderer`, `rules`, or `adjudicator` — perception does not get to see the judgement machinery.

## 6. Integration contracts

| Boundary | Contract | Direction |
|---|---|---|
| note → extractor | `masked_text: str` + `vocabulary: list[str]` → `ExtractionRecord` | in |
| extractor → rules | `ExtractionRecord` (raw strings only; **no** `dose_mg_per_day`, **no** `severity`) | in |
| rules → adjudicator | `list[CandidateFinding]` with `rule_id` + `table_version` always set | in |
| adjudicator → renderer | `AdjudicationResult` (frozen: verdict, findings, coverage) | in |
| adjudicator → audit | `AuditRecord` (no case text, `input_hash` only) | out |
| renderer → caller | `advisory_text: str`, ≤ 200 words, every sentence traceable | out |

Any new field crossing a boundary is a contract change → ADR. The extractor's contract deliberately has **no place** to put a verdict; if you find yourself wanting one, you are about to violate INV-003.

## 7. Verification requirements the generated code must satisfy

Before you report a change complete:

1. `python scripts/validate_requirements.py` → PASS (schema gate).
2. `python -m pytest test/offline -q` → all green, and **the full prior suite** runs, not just your new tests (regression gate).
3. Every new behaviour has a test written **before** the implementation, referencing its `REQ-*` id in the test docstring.
4. Every invariant you touched has a **negative** test that fails if the invariant is removed (mutation check).
5. `python scripts/check_permissions_sync.py` and `python scripts/check_ai_use_log.py` → PASS.
6. `docs/ai-use-log.yaml` updated in the same change if you touched `src/` or `prompts/`.
7. Self-verification output pasted into the session, not summarised as "all tests pass".

## 8. Hard stops

Stop and ask a human when:

- a requirement is ambiguous or two requirements conflict;
- a change would touch a safety-critical module without an ADR;
- a test cannot be made to fail after you believe the behaviour is broken (the test is wrong, or the behaviour is not where you think);
- you are about to add a dependency;
- you are about to relax, skip, or `xfail` an invariant test. **This is never permitted** — report it instead.
