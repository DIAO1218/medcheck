# Technical Debt Register

Debt in the AI era is not only "code we should refactor". It is also the ways an
agent-assisted build drifts: rules that age badly, dependencies that were never
real, code nobody dares touch, and evaluation that measures the rubric instead of
the product. Each row names its category, its interest (what it costs if left),
and the trigger that forces repayment.

| Category key | Meaning in this project |
|---|---|
| `prompt rot` | a rule, prompt, or governance file that has fallen behind the requirements |
| `hallucinated dependency` | a library or API assumed to exist / behave as the agent claimed |
| `untouchable code` | code that is correct-ish but too risky to modify, so it ossifies |
| `hidden dependency` | coupling that is not visible in the import graph |
| `agent-induced bloat` | structure that exists because the agent produced it, not because it is needed |
| `evaluation debt` | quality is asserted or proxied rather than measured |
| `guardrail debt` | a control that exists but is weaker than it appears |
| `human/cognitive debt` | knowledge that lives only in one head or in the transcript |

---

## Open

| # | Category | Item | Interest if unpaid | Repayment trigger | Owner |
|---|---|---|---|---|---|
| **DEBT-01** | evaluation debt | Quality scores come from `scripts/eval_replay.py`, which computes **proxy** metrics (statement traceability, rule resolvability), not a human-judged rubric. Faithfulness 1.0 is therefore partly circular. | We could ship a regression against a real rubric while the proxy stays at 1.0. | First sprint close: 20% human audit of the frozen set; disagreement rate > 10% replaces the proxy with a judged set. | verify |
| ~~DEBT-02~~ | evaluation debt | ~~6-case set~~ **repaid at S0 close: 25 cases pinned by `test_fixture_matrix.py`.** Residual risk moved to DEBT-11. | — | — | verify |
| **DEBT-03** | guardrail debt | `extractor.llm._last_json_object` takes the **last** balanced JSON object in the response and ignores everything before it. Tolerant by design (the course gateway wraps answers in prose), but it could select a JSON object that is not the answer. | A malformed-but-parseable response is accepted as extraction. | When a response is observed to contain two objects, tighten to "last object with a `medications` key" and add a fixture. | build |
| **DEBT-04** | hidden dependency | `rules.loader.get_tables()` is process-cached by directory path. A test that mutates tables on disk reads a stale table and silently passes. | A table test proves yesterday's data. | Any test that needs a modified table must call `load_tables()`; enforce with a lint note + a comment in `conftest.py`. | build |
| **DEBT-05** | untouchable code | `contracts.py` is frozen: `ExtractionRecord`/`Finding` changes ripple into every module. Nobody will want to touch it, so the extractor schema will drift by accretion in `unparsed` strings instead of fields. | The contract becomes a comment field, and INV-003's protection weakens by erosion rather than by edit. | When `unparsed` carries more than 5 distinct categories, propose ADR-002 for a typed `UnparsedItem`. | architecture |
| **DEBT-06** | prompt rot | `prompts/prompt_v1.0.yaml` and `v1.1.yaml` exist, but the offline suite exercises `heuristic`, so the **prompts are untested**. | The prompt is the least verified artefact in a system whose thesis is verification. | First live run: record accuracy per prompt version in the evaluation logbook; gate 4 on prompt change becomes meaningful. | build |
| **DEBT-07** | human/cognitive debt | The rule tables are teaching data with no clinical reviewer. `data/rules/ddi.yaml` rows cite a "basis" class, not a source document. | The system's real-world validity is unknown, and INV-001 keeps it honest by holding, which hides the gap behind a large HOLD rate. | Any claim about clinical plausibility in the report must be qualified; if the project continues, a pharmacist review is the first task. | domain |
| **DEBT-08** | agent-induced bloat | `runtime-policy-catalog.md` defines 22 failure paths; only 11 have code. The rest describe intent. | A reader mistakes a catalogue entry for an implemented behaviour. | Each unimplemented row must carry `status: planned` before the next sprint close. | process |
| **DEBT-09** | guardrail debt | Only 2 of 5 invariant guards are mutation-verified (INV-001, INV-003). INV-002/004/005 are asserted by tests but their deletion has not been shown to break anything. | A guard could be dead code, and we would not know. | Sprint 1: run the mutation check for the remaining three, record in `verification-constraints.md` §3. | verify |
| **DEBT-13** | hallucinated dependency | The S0 agent built the extractor against an assumed provider contract: a `content` field holding JSON, and a response containing exactly one JSON object. The course gateway puts the answer in `reasoning_content` with `content` empty, and wraps it in prose. | The adapter would have parsed an empty string on the first live call and reported "model returned nothing" — a bug that looks like a model failure and is actually an assumption failure. | Any new external contract must have one recorded real response in `test/fixtures/responses/` before the adapter is merged. | build |
| **DEBT-11** | evaluation debt | The set is 25 cases, all written by the team, and 14 of them hold for the same reason (coverage gap or renal data). | Gate 4 can pass while a whole failure family is untested; a regression in HOLD-with-gap logic is over-covered, a regression in APPROVE is under-covered. | Add 10 cases from outside the team's own imagination (e.g. generated multi-drug combinations) before the first live release. | verify |
| **DEBT-10** | untouchable code | `test/offline/test_cli.py` spawns a subprocess per case (6 cases → 6 processes). Slow and awkward to debug, but nobody wants to refactor the path that proves the CLI contract. | Test suite time grows linearly with fixture count. | When suite time exceeds 30 s, share one process via `main(argv)` in-process. | build |

## Repaid

| # | Item | Repaid by | Date |
|---|---|---|---|
| DEBT-02 | evaluation set grown from 6 to 25 cases, each pinned verdict + codes, no PHI in fixtures | T5 session; `test_fixture_matrix.py`; logbook E-08 | 2026-11-14 |

## Rules for this register

1. A row is added in the same PR that creates the debt, or it is not added at all.
2. "Interest" must be a concrete cost (a wrong verdict class, a slow suite, a claim we cannot support), not "maintainability".
3. A repayment trigger must be observable. "When we have time" is not a trigger.
4. Repaid rows move to the bottom table with the PR that repaid them; they are never deleted, because the pattern of what we accumulated is itself evidence.
