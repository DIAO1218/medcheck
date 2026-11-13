# Verification Constraints

The rules the verification agent applies. These are the operational form of
`REQ-Q-*`, `REQ-S-*` and the five invariants; the trace matrix names the test for
each requirement.

---

## 1. Four non-negotiables

1. **Every fit criterion has at least one test.** A requirement without a test is an intention.
2. **Every invariant has at least one test that fails when the invariant is violated.** A test that passes in both worlds proves nothing.
3. **Every test references the requirement or invariant it verifies** — in the docstring, as `REQ-x-nnn` or `INV-00n`.
4. **Every round runs all prior suites.** Green-on-the-new-tests with a broken old test is a regression, and regressions block.

## 2. Three tiers

| Tier | What it proves | Where | Blocking? |
|---|---|---|---|
| **Structural** | imports, module boundaries, permissions, single-authority sites, requirement traceability | `test/offline/test_structure.py`, `test/offline/test_dependencies.py`, `scripts/check_permissions_sync.py` | yes (gate 2) |
| **Regression** | all prior behaviour still holds, invariants at zero violations | `test/offline/` (194 tests at S0 close) | yes (gate 5) |
| **Behavioural** | semantic quality (faithfulness ≥ 0.90, relevance ≥ 0.85), zero safety escapes | `scripts/eval_replay.py`, invariant suites | yes (gate 4) |

## 3. The mutation check

For every invariant touched by a change, the reviewer asks: *if I delete the guard, does a test go red?* This is recorded per sprint in `docs/architecture/evaluation-logbook.md`.

S0 results (verified by hand, commands in §6):

| Guard deleted | Test that failed | Verdict |
|---|---|---|
| `coverage.assess` unknown-drug branch | `test_inv001_unknown_drug_is_not_approved` | load-bearing |
| `assert_ceiling` no-silent-overdose branch | `test_inv002_asserted_dose_above_ceiling_rejected` | load-bearing |
| `_assert_no_authority` in `from_payload` | `test_inv003_model_verdict_rejected` (10 params) | load-bearing |
| `strict` residual/unclassified scan in `mask` | `test_masking_failure_blocks_the_call` | load-bearing |
| `Finding.__post_init__` rule-id check | `test_inv005_missing_rule_id_aborts` | load-bearing |

A guard whose deletion breaks nothing is either untested or unnecessary — both are findings for the debt register.

## 4. Test layout

```
test/
├── offline/          deterministic, no network, no model -- runs on every PR
│   ├── test_units.py           REQ-F-002
│   ├── test_ddi.py             REQ-F-003
│   ├── test_dose.py            REQ-F-004
│   ├── test_extractor_contract.py  REQ-F-001
│   ├── test_adjudicator.py     REQ-F-005
│   ├── test_renderer.py        REQ-F-006, REQ-Q-002
│   ├── test_audit.py           REQ-F-007
│   ├── test_cli.py             REQ-F-008
│   ├── test_invariants.py      INV-001..005 (negative tests)
│   ├── test_privacy.py         INV-004
│   ├── test_context_assembly.py  REQ-C-001
│   ├── test_permissions.py     REQ-G-002
│   ├── test_structure.py       structural tier
│   ├── test_dependencies.py    REQ-S-001, REQ-S-002
│   ├── test_semantic_gate.py   REQ-Q-001
│   ├── test_requirements_schema.py  gate 3 self-test
│   ├── test_gates_selftest.py  gates 1, 6 self-test
│   ├── test_fixture_matrix.py  the 25-case frozen set, pinned per verdict
│   └── test_perf.py            REQ-P-001
├── live/             requires a model endpoint; marked `live`, never in CI gate 5
└── fixtures/         synthetic notes, cases, the generated DDI corpus
```

**Fixture rules:** synthetic only (no real patient data), generated corpora committed with their generator, and a fixed random seed for any property test (`20261114`).

## 5. Quality bar for a PR

| Check | Threshold |
|---|---|
| Offline suite | 100% pass, zero skipped invariants |
| New code coverage of new branches | every new branch has a test, or a debt entry explaining why not |
| Semantic scores | faithfulness ≥ 0.90, relevance ≥ 0.85 |
| Invariant violations | exactly 0 |
| p95 adjudication | ≤ 50 ms |
| Advisory length | ≤ 200 words, 100% of cases |
| New dependencies | allowlisted, permissive licence, human-approved |
| AI-use log | updated in the same PR |

## 6. Commands the verification agent runs

```bash
python scripts/validate_requirements.py      # gate 3
python -m pytest test/offline -q             # gates 2 + 5
python scripts/eval_replay.py                # gate 4
python scripts/check_permissions_sync.py     # gate 2 (safety-relevant PRs)
python scripts/check_test_approval.py --changed <files>   # gates 1 + 6
python scripts/check_ai_use_log.py --changed <files>      # gate 6
python scripts/build_ddi_fixtures.py --check              # fixtures not stale
```

Raw output is pasted into the review memo. "All tests pass" without output is not evidence.

## 7. What verification is not allowed to do

- Skip or `xfail` an invariant test. If it is red, the code is wrong.
- Loosen a threshold to make a gate pass. Thresholds live in the registry (`REQ-Q-001`) and changing one is a requirements change with an ADR.
- Approve its own change: the `verify-agent` role cannot write `src/` (permission model §1).
- Treat a green CI as approval. CI proves the mechanical constraints; the review memo carries the judgement, and it ends in APPROVE / CHANGES REQUIRED / REJECT.
