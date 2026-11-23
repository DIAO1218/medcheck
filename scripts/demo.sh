#!/usr/bin/env bash
# Demo driver for the 10-minute video and the in-person presentation.
#
#   bash scripts/demo.sh              # pauses between steps, for recording
#   bash scripts/demo.sh --no-pause   # runs straight through, for rehearsal
#
# Every command here is READ-ONLY: it runs the test suite, the CLI on frozen
# fixtures, and the gate scripts. Nothing is mutated, so this is safe to run on
# the real working tree. The before/after mutations live in
# docs/zh/demo-before-after.zh.md and must be done in a copy of the repository.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

# The CLI is run as a module, so src/ must be importable even when the package is
# not pip-installed. Keeping this here means the demo works on a fresh clone.
# On Windows the native interpreter needs a Windows-style path, so convert it
# when cygpath is available (Git Bash provides it).
if command -v cygpath >/dev/null 2>&1; then
  export PYTHONPATH="$(cygpath -w "$ROOT/src")"
else
  export PYTHONPATH="$ROOT/src"
fi

PAUSE=1
[ "${1:-}" = "--no-pause" ] && PAUSE=0

step() {
  printf '\n\033[1;36m── %s ──\033[0m\n' "$1"
  if [ "$PAUSE" -eq 1 ]; then
    printf '按回车继续…'
    read -r _
  fi
}

note() { printf '\033[0;33m%s\033[0m\n' "$1"; }

step "0 · 环境确认（约 2 秒）"
note "PYTHONPATH=$PYTHONPATH   （CLI 以模块方式运行，需要 src/ 在路径上）"
python -V

step "1 · 全套离线测试（约 8 秒）"
note "预期：199 passed"
python -m pytest test/offline -q

step "2 · 产品演示之一：APPROVE"
note "预期：verdict = APPROVE，findings = [SYS-PASS-001 / ALL_CHECKS_PASSED]"
python -m medcheck.api.cli --case test/fixtures/cases/c01_approve_single.json

step "3 · 产品演示之二：BLOCK"
note "预期：verdict = BLOCK，findings = [DDI-007 / DDI_CONTRAINDICATED]"
python -m medcheck.api.cli --case test/fixtures/cases/c04_block_contraindicated.json

step "4 · 产品演示之三：HOLD（讲述重点）"
note "预期：verdict = HOLD，findings = [SYS-RENAL-001 / RENAL_DATA_MISSING]"
note "台词：BLOCK 会断言「剂量过高」，而我们只知道「无法评估」。"
python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json

step "5 · 覆盖缺口：HOLD 而不是 APPROVE"
note "预期：verdict = HOLD，coverage_complete = false，COVERAGE_GAP"
python -m medcheck.api.cli --case test/fixtures/cases/c12_hold_coverage_hole.json

step "6 · 可追溯：需求注册表过 schema 门"
note "预期：PASS: 25 requirements (5 invariants)"
python scripts/validate_requirements.py

step "7 · 可追溯：每个测试必须写需求编号"
note "这条结构测试会遍历 test/ 下所有测试函数的 docstring"
python -m pytest test/offline/test_structure.py -q

step "8 · 语义评估门（25 例冻结集）"
note "预期：faithfulness 1.0 / relevance 1.0，PASS"
python scripts/eval_replay.py

step "9 · 权限模型与架构一致"
note "预期：PASS: permission model is deny-by-default and consistent with the blueprint"
python scripts/check_permissions_sync.py

step "10 · 门 1 的 ADR 检查（这一步预期 FAIL，是演示重点）"
note "改冻结契约但本次改动里没有 ADR → 门 1 拒绝。"
note "预期输出以 FAIL: safety-relevant change without a new or amended ADR … (gate 1) 开头"
python scripts/check_test_approval.py --changed src/medcheck/contracts.py || true
note "对照：只改文档时不应要求 ADR ——"
python scripts/check_test_approval.py --changed docs/zh/README.md

step "11 · 收尾：再说一次数字"
note "199 项离线测试 / 25 条需求 5 条不变量 / 25 例冻结评估集 / 六道阻断门"
printf '\n演示结束。\n'
