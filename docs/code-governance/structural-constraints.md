# Structural Constraints

Module organisation rules for the coding agent. These are enforced by
`test/offline/test_structure.py` (architectural fitness functions), not by
review discipline — a rule that only exists in prose is a rule that erodes.

---

## 1. One element, one module

| Architectural element (`architecture-blueprint.md` §4) | Module | Status |
|---|---|---|
| `privacy` | `src/medcheck/privacy/` | safety-critical |
| `extractor` | `src/medcheck/extractor/` | modifiable |
| `rules.units` | `src/medcheck/rules/units.py` | safety-critical |
| `rules.ddi` | `src/medcheck/rules/ddi.py` | safety-critical |
| `rules.dose` | `src/medcheck/rules/dose.py` | safety-critical |
| `rules.loader` | `src/medcheck/rules/loader.py` | safety-critical |
| `adjudicator` | `src/medcheck/adjudicator/{verdict,coverage,guard}.py` | safety-critical |
| `renderer` | `src/medcheck/renderer/template.py` | modifiable |
| `audit` | `src/medcheck/audit/log.py` | safety-critical |
| `api.cli` | `src/medcheck/api/cli.py` | modifiable |
| boundary types | `src/medcheck/contracts.py` | **frozen** |
| orchestration | `src/medcheck/pipeline.py` | modifiable |

**Rules**

1. A component may not be split across modules, and a module may not contain two components.
2. `contracts.py` and `pipeline.py` are infrastructure, not components; they may be extended only with an ADR (contract) or a test (pipeline order).
3. Adding a module that is not in this table is a design change: propose an ADR amendment, do not just create the file.

## 2. Import direction

```
api ──► renderer ──► contracts
 │        (no adjudicator internals)
 ├──► audit ──► contracts
 └──► adjudicator ──► rules ──► contracts
          │              │
          └──────────────┴──► privacy ──► contracts

extractor ──► contracts            (and nothing else)
```

Enforced forbiddances:

| Module | May not import | Why |
|---|---|---|
| `extractor` | `rules`, `adjudicator`, `audit`, `renderer`, `api` | Perception must not see the judgement machinery; a model-adjacent module that can read rule tables can be prompt-injected into describing them |
| `privacy` | everything except `contracts` | Masking must not depend on domain logic |
| `rules` | `adjudicator`, `audit`, `renderer`, `api`, `extractor`, `privacy` | Rules are pure table lookups |
| `renderer` | `adjudicator`, `rules`, `audit`, `extractor`, `privacy` | The advisory is a terminal sink; it receives a finished result |
| any module | `api` | Entry points are leaves |

`test_no_authority_import` walks the AST of every module and fails on a violation. It also catches the common workaround of importing a sibling through `__init__`.

## 3. Extension, never replacement

New work extends the baseline:

- add a rule to `data/rules/*.yaml` and a test that proves it — do not edit the matcher to special-case a drug;
- add a finding code to `contracts.py` and to `verdict.py`'s precedence table — do not branch inside `renderer`;
- add a runtime policy row to `runtime-policy-catalog.md` and implement it in `pipeline.py` — do not swallow the error and return `HOLD` silently.

A PR that deletes a module, renames a component, or changes a contract field is an architecture change and requires an ADR.

## 4. Every module and function cites its constraint

Every public function carries, in its docstring, the requirement or invariant it implements. Example:

```python
def assess(medications, tables) -> CoverageReport:
    """Coverage assessment: the fail-closed heart of INV-001. ..."""
```

`test_every_requirement_is_traced` closes the loop from the other side: every `REQ-*` in the registry must appear in at least one test file.

## 5. Authority boundaries in code

| Boundary | Code-level enforcement |
|---|---|
| No model-authored verdict | `ExtractionRecord` has no such field; `from_payload` raises `AuthorityViolation` on a forbidden key at any depth |
| Single APPROVE site | only `adjudicator/verdict.py` may contain `verdict = Verdict.APPROVE` (asserted by `test_single_approve_site`) |
| Single result composer | only `adjudicator/verdict.py` may construct `AdjudicationResult` |
| Frozen results | `Finding` and `AdjudicationResult` are frozen dataclasses |
| Ceilings are not editable | `assert_ceiling` recomputes the ceiling from the table and compares |

## 6. Test independence

- At least one **negative** test per feature: the test must fail when the feature's guard is removed.
- Invariant tests may not import private helpers to reach a state the public API forbids; they construct the violation deliberately and assert the refusal.
- No test may call a live model. Live tests live in `test/live/` and are marked `live`.
- A test may not assert on a mock's behaviour as a substitute for the system's behaviour.

## 7. Change policy reminders

Changes under `src/medcheck/{adjudicator,rules,privacy,audit}` need: an ADR id in the PR body, a human approval, and a green invariant suite. `data/rules/**` is not writable by any agent — propose a diff in a PR comment.
