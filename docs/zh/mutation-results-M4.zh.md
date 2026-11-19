# DEBT-09 变异检验结果 — M4

[English version](../mutation-results-M4.md)

检验日期：2026-11-18。姓名、学号待填写。

| # | 不变量 | 变异位置 | 基线 | 变异后 | 失败测试 | 结论 |
|---|---|---|---|---|---|---|
| 1 | INV-002 剂量上限完整性 | `verdict.py:110`，阈值从 `1e-9` 放宽到 `1e9` | 199 passed | 1 failed, 198 passed | `test_inv002_ceiling_cannot_be_raised_at_runtime` | 承重 |
| 2 | INV-002 不得静默超量 | `verdict.py:119`，临时禁用缺少超量发现的检查 | 199 passed | 1 failed, 198 passed | `test_inv002_asserted_dose_above_ceiling_rejected` | 承重 |
| 3 | INV-004 脱敏失败必须拦截 | `mask.py:80`，临时禁用严格检查 | 199 passed | 1 failed, 198 passed | `test_masking_failure_blocks_the_call` | 承重 |
| 4 | INV-005 发现须有规则编号和表版本 | `contracts.py:203,205`，临时禁用两个非空检查 | 199 passed | 2 failed, 197 passed | `test_inv005_missing_rule_id_aborts`、`test_inv005_missing_table_version_aborts` | 承重 |
| 5 | INV-005 引用的规则必须存在 | `verdict.py:76`，临时让未知规则不再抛出异常 | 199 passed | 2 failed, 197 passed | `test_inv005_unresolvable_rule_aborts`、`test_inv005_compose_refuses_unresolvable_finding` | 承重 |

结论：五项变异全部被现有测试捕捉，未发现漏过的变异。检验 5 比任务说明预期多失败一项：除了直接验证规则解析的测试，裁决组装层也拒绝了无法解析的发现。

## 检验 1 原始失败摘要

```text
E       Failed: DID NOT RAISE Exception
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv002_ceiling_cannot_be_raised_at_runtime
1 failed, 198 passed in 3.45s
```

## 检验 2 原始失败摘要

```text
E       Failed: DID NOT RAISE Exception
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv002_asserted_dose_above_ceiling_rejected
1 failed, 198 passed in 7.02s
```

## 检验 3 原始失败摘要

```text
E       Failed: DID NOT RAISE MaskingError
=========================== short test summary info ===========================
FAILED test/offline/test_privacy.py::test_masking_failure_blocks_the_call - F...
1 failed, 198 passed in 4.04s
```

## 检验 4 原始失败摘要

```text
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv005_missing_rule_id_aborts - ...
FAILED test/offline/test_invariants.py::test_inv005_missing_table_version_aborts
2 failed, 197 passed in 3.85s
```

## 检验 5 原始失败摘要

```text
=========================== short test summary info ===========================
FAILED test/offline/test_invariants.py::test_inv005_unresolvable_rule_aborts
FAILED test/offline/test_invariants.py::test_inv005_compose_refuses_unresolvable_finding
2 failed, 197 passed in 4.01s
```

## 还原确认

每项变异均在下一项开始前还原，完整离线套件依次恢复为 `199 passed`，耗时分别为 3.38s、3.79s、3.94s、4.08s、3.98s。最终 `git diff --exit-code -- src test` 无差异，`git status --short` 仅列出本报告。未提交任何变异代码。
