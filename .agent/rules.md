# .agent/rules.md — the project covenant

> **Human-only file.** This is the agreement between the team and the coding agent. Agents may read it and must follow it; they may not edit it.

## 1. Abstraction limits

- **One level of indirection, maximum.** A module may call a rule function directly. No registry-of-factories, no plugin bus, no generic `Rule` protocol unless a second concrete implementation already exists in the repo.
- **No speculative generality.** If a feature is not required by a `REQ-*` id, it does not go in.
- **No new module for convenience.** New behaviour lives in the module that already owns the element (structural constraints §1).
- **Three similar lines beat a premature helper.** Duplication is cheaper to review than an abstraction that turned out wrong.

## 2. Dependency constraints

- No runtime dependency outside `requirements.txt`, and `requirements.txt` changes need human approval (REQ-S-002).
- Standard library first. `urllib` over `requests`; `dataclasses` over `attrs`; `json` over `orjson`.
- `src/` may import only `medcheck.*` and stdlib plus the allowlist (`yaml` in rules/loader). A model SDK is **not** a dependency: the extractor speaks HTTP.
- No test may depend on a network call. Live tests are marked `live` and never run in gate 5.

## 3. Test independence

- At least one **negative** test per feature: the test must fail when the guard is deleted.
- Invariant tests construct the violation deliberately; they do not reach into private state to simulate one.
- No test asserts on a mock's behaviour as a proxy for the system's behaviour.
- Fixtures are synthetic and committed; generated corpora carry their generator and a seed.

## 4. Safety-critical change procedure

A change to `src/medcheck/{adjudicator,rules,privacy,audit}` requires, in this order:

1. an **ADR** (new, or an amendment naming which driver moved) — agents may draft it in a PR comment, only a human commits it;
2. the **test plan approved** in `docs/test-approvals.yaml` before implementation;
3. a **human reviewer** named on the PR;
4. a **green full invariant suite** with the mutation check recorded.

Skipping any of the four is a rejected PR, regardless of how good the code is.

## 5. Context freshness

- If a requirement changes, the rules and `AGENTS.md` must be updated **within one sprint**.
- Staleness is measured: compare `docs/req/requirements.yaml` `last_updated` against the last commit touching `AGENTS.md`. If the gap exceeds one sprint, the debt register gains a `prompt rot` row and the next PR is blocked until refreshed.
- A stale rule is worse than a missing rule: it is wrong with authority.

## 6. Honesty clauses

- Do not describe work as verified without pasted output.
- Do not mark a task complete with a known-failing test, a skipped test, or an unrun mutation check.
- Do not reconstruct a transcript after the session; the transcript is evidence (D5), and a reconstructed one is fabrication.
- If the agent's output was used nearly verbatim, the AI-use log says so. The log is not a formality — it is the record of what was delegated.

## 7. What the covenant does not do

It does not promise the agent will be right. It promises that when the agent is wrong, the wrongness lands somewhere visible: a red gate, a failing invariant, a held case — never in an `APPROVE` that nobody checked.
