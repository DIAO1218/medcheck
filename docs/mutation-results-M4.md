# DEBT-09 Mutation Test Results — M4

[中文对照版](zh/mutation-results-M4.zh.md)

Test date: November 18, 2026. Name and student ID pending.

| # | Invariant | Temporary mutation | Baseline | Mutated result | Failing tests | Conclusion |
|---|---|---|---|---|---|---|
| 1 | INV-002 Dose ceiling integrity | Raised the threshold from `1e-9` to `1e9` in `verdict.py:110` | 199 passed | 1 failed, 198 passed | `test_inv002_ceiling_cannot_be_raised_at_runtime` | Detected |
| 2 | INV-002 Excess doses must be reported | Disabled the check for a missing excess-dose finding in `verdict.py:119` | 199 passed | 1 failed, 198 passed | `test_inv002_asserted_dose_above_ceiling_rejected` | Detected |
| 3 | INV-004 Masking failures must stop processing | Disabled strict masking checks in `mask.py:80` | 199 passed | 1 failed, 198 passed | `test_masking_failure_blocks_the_call` | Detected |
| 4 | INV-005 Findings require a rule ID and table version | Disabled both required-field checks in `contracts.py:203,205` | 199 passed | 2 failed, 197 passed | `test_inv005_missing_rule_id_aborts`, `test_inv005_missing_table_version_aborts` | Detected |
| 5 | INV-005 Referenced rules must exist | Suppressed the exception for unknown rules in `verdict.py:76` | 199 passed | 2 failed, 197 passed | `test_inv005_unresolvable_rule_aborts`, `test_inv005_compose_refuses_unresolvable_finding` | Detected |

The existing tests detected all five mutations. Check 5 triggered one more failure than the task brief predicted. Both the rule lookup test and the verdict composition test detected the missing rejection.

## Check 1 — pytest failure summary

```text
E       Failed: DID NOT RAISE Exception
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv002_ceiling_cannot_be_raised_at_runtime
1 failed, 198 passed in 3.45s
```

## Check 2 — pytest failure summary

```text
E       Failed: DID NOT RAISE Exception
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv002_asserted_dose_above_ceiling_rejected
1 failed, 198 passed in 7.02s
```

## Check 3 — pytest failure summary

```text
E       Failed: DID NOT RAISE MaskingError
=========================== short test summary info ===========================
FAILED test/offline/test_privacy.py::test_masking_failure_blocks_the_call - F...
1 failed, 198 passed in 4.04s
```

## Check 4 — pytest failure summary

```text
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv005_missing_rule_id_aborts - ...
FAILED test/offline/test_invariants.py::test_inv005_missing_table_version_aborts
2 failed, 197 passed in 3.85s
```

## Check 5 — pytest failure summary

```text
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv005_unresolvable_rule_aborts
FAILED test/offline/test_invariants.py::test_inv005_compose_refuses_unresolvable_finding
2 failed, 197 passed in 4.01s
```

## Restoration verification

Each mutation was reverted before the next check. All 199 offline tests passed after each restoration, in 3.38 s, 3.79 s, 3.94 s, 4.08 s, and 3.98 s, respectively. The final `git diff --exit-code -- src test` found no changes. No mutated code was committed.
