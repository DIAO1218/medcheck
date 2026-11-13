# .opencode/rules.md — always-on behavioural rules

> **Human-only file.** No agent role may write this file (permission model §5). Changes require a human commit and, if they weaken a constraint, an ADR.

These rules load on every session, before any task. They are short on purpose: a rule nobody remembers is a rule nobody follows.

## 1. The five things that are never true of MedCheck output

1. A verdict that came from a model.
2. A dose that no deterministic table produced.
3. An `APPROVE` without a coverage proof and an explicit pass finding.
4. A finding without a `rule_id` and `table_version`.
5. Prose that contains a number, drug, or severity not present in the findings.

If your change makes any of these possible, stop and report it. Do not implement around it.

## 2. Working rules

| # | Rule | Why |
|---|---|---|
| R1 | Read `AGENTS.md` then `architecture-blueprint.md` before touching code | The blueprint outranks your plan |
| R2 | Plan first, stop for approval, then tests, then code | `Prompt.md` defines the gates |
| R3 | Tests before implementation; a failing test must fail for the right reason | Prevents "test written to match the code" |
| R4 | Never weaken a test to make it pass | `skip`, `xfail`, loosened assertion, mock that returns the expectation |
| R5 | Never modify anything under `.opencode/`, `.agent/`, `.github/workflows/`, `docs/architecture/`, `data/rules/` | Human-only surfaces |
| R6 | Never add a dependency | Allowlist is closed (REQ-S-002) |
| R7 | Paste raw command output when claiming verification | A summary is not evidence |
| R8 | If a requirement is ambiguous, ask. Do not infer a requirement | Ambiguity resolved by guessing is a defect with a delay |
| R9 | Log every substantial session in `docs/ai-use-log.yaml` in the same PR | Gate 6 blocks otherwise |
| R10 | When you notice debt you are not fixing, add a row to `docs/debt-register.md` | Debt that is not written down is debt that is forgotten |
| R11 | Keep the advisory ≤ 200 words and never let it change the verdict | REQ-Q-002, REQ-F-006 |
| R12 | Do not touch `data/audit/**`, `data/state/**`, `data/cache/**` | Case-derived data; INV-004 |

## 3. Stop-and-ask triggers

Stop the session and ask a human when:

- a change would touch a safety-critical module (`adjudicator`, `rules`, `privacy`, `audit`) without an ADR id;
- two requirements conflict, or a requirement is not machine-checkable as written;
- a test cannot be made to fail after you believe the behaviour is broken;
- you believe an invariant should be relaxed (answer: it should not — report instead);
- you are about to delete or rename a module.

## 4. Tone of a hand-off

Report facts, not confidence:

- files changed, with one line each on why;
- requirements closed and the tests that prove them;
- invariants touched and the mutation check you ran;
- what you did **not** do, and why;
- what you are unsure about.

"I believe this works" is not a hand-off. "Here is the output" is.
