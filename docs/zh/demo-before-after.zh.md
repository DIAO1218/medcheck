# 三组「前后对比」的复现步骤

> 视频段 3 用这三组。每组都能在 **30 秒内**复现，且不需要网络、不需要模型。
> 所有命令与输出已实测（2026-11-23）。

---

## 0. 铁律

**在副本里改，不在真仓库改。** 一次录制要改三次源码，任何一次忘记还原，都会让后续测试莫名其妙地失败。

```bash
cd "C:/Users/26657/Desktop/CS5351/GROUP PROJECT"
rm -rf /tmp/mcdemo
cp -r MedCheck /tmp/mcdemo      # 连 .git 一起复制，还原用 git checkout
cd /tmp/mcdemo
pip install -e ".[dev]" 2>/dev/null || true
```

`/tmp/mcdemo` 里有完整的 `.git`，所以每一次还原都可以用：

```bash
git checkout -- src/medcheck/adjudicator/coverage.py
git status --porcelain          # 应为空
```

---

## 组 1｜BUG-0002：覆盖缺口被当成「没有相互作用」

**为什么重要**：这是 fail-open 的典型——把「表里没写」读成「没有风险」。

### 左边：错误行为（关掉空洞检查）

```bash
python - <<'PY'
import pathlib
p = pathlib.Path("src/medcheck/adjudicator/coverage.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        if tables.is_hole(first, second):",
    "        if False:  # MUTATION: hole check disabled",
    1,
)
p.write_text(s, encoding="utf-8")
PY

PYTHONPATH=src python -m medcheck.api.cli --case test/fixtures/cases/c12_hold_coverage_hole.json
```

实测输出（关键字段）：

```json
{
  "case_id": "c12_hold_coverage_hole",
  "coverage_complete": true,
  "findings": [{ "code": "ALL_CHECKS_PASSED", "rule_id": "SYS-PASS-001" }],
  "verdict": "APPROVE"
}
```

> 二甲双胍 + 环丙沙星。这一对在表里被声明为「未评估」，但现在系统批准了它。

### 右边：现在行为（还原）

```bash
git checkout -- src/medcheck/adjudicator/coverage.py
PYTHONPATH=src python -m medcheck.api.cli --case test/fixtures/cases/c12_hold_coverage_hole.json
```

```json
{
  "coverage_complete": false,
  "findings": [{
    "code": "COVERAGE_GAP",
    "rule_id": "SYS-COVERAGE-001",
    "statement": "the pair ciprofloxacin + metformin is declared unassessed in table …; interaction status unknown"
  }],
  "verdict": "HOLD"
}
```

**台词**：`Not in the table was being read as no interaction. Now the table declares its own holes, and a hole can never be approved.`

---

## 组 2｜BUG-0004：缺失的肾功能被当成「最保守档」

**为什么重要**：拦截听起来更安全，但它断言了「剂量过高」，而我们只知道「不知道」。

### 左边：错误行为（把缺失 eGFR 当 G5 档比较）

```bash
python - <<'PY'
import pathlib
p = pathlib.Path("src/medcheck/rules/dose.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '        if row.get("renal_sensitive") and egfr is None:',
    '        if False:  # MUTATION: band a missing eGFR as the most conservative',
    1,
)
p.write_text(s, encoding="utf-8")
PY

PYTHONPATH=src python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json
```

实测输出：

```json
{
  "findings": [{
    "code": "DOSE_CEILING",
    "rule_id": "DOSE-009",
    "statement": "digoxin at 0.125 mg/day exceeds the G5 ceiling of 0.062 mg/day"
  }],
  "verdict": "BLOCK"
}
```

> 注意那句 `exceeds the G5 ceiling`：我们把「没有肾功能数据」偷偷变成了「肾功能最差」。

### 右边：现在行为

```bash
git checkout -- src/medcheck/rules/dose.py
PYTHONPATH=src python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json
```

```json
{
  "findings": [{
    "code": "RENAL_DATA_MISSING",
    "rule_id": "SYS-RENAL-001",
    "statement": "digoxin is renally cleared and no eGFR was recorded; the dose ceiling was not evaluated and the case is held"
  }],
  "verdict": "HOLD"
}
```

**台词**：`Blocking would assert the dose is too high. We only know we cannot evaluate it. Hold says what is true.`

---

## 组 3｜BUG-0012：门禁只检查 ADR「存在」，不检查「新鲜」

**为什么重要**：这是唯一一个缺陷发生在**门禁本身**上的例子，而且它是由人读别人的 PR 发现的。

### 左边：门禁失效（关掉 fresh-ADR 检查）

```bash
python - <<'PY'
import pathlib
p = pathlib.Path("scripts/check_test_approval.py")
s = p.read_text(encoding="utf-8")
old = """    if safety_hits and not adrs_touched(changed):
        problems.append(
            "safety-relevant change without a new or amended ADR under "
            f"{ADR_DIR} (gate 1): " + ", ".join(safety_hits[:3])
        )"""
assert old in s
s = s.replace(old, "    if False:  # MUTATION: fresh-ADR check disabled", 1)
p.write_text(s, encoding="utf-8")
PY

python scripts/check_test_approval.py --changed src/medcheck/contracts.py
```

实测输出：

```
PASS: test-approval + ADR gates (1 changed file(s))
```

> 冻结的 `contracts.py` 被改写，没有任何 ADR，门却放行——因为台账里记着基线 ADR-001。

### 右边：现在行为

```bash
git checkout -- scripts/check_test_approval.py
python scripts/check_test_approval.py --changed src/medcheck/contracts.py; echo "exit=$?"
```

```
FAIL: safety-relevant change without a new or amended ADR under docs/architecture/adr/ (gate 1): src/medcheck/contracts.py
exit=1
```

对照：只改文档时不该要 ADR——

```bash
python scripts/check_test_approval.py --changed docs/zh/README.md
# PASS: test-approval + ADR gates (1 changed file(s))
```

**台词**：`The gate asked whether an ADR existed, not whether a decision was made now. We fixed the gate — not the pull request.`

---

## 录制技巧

| 做法 | 原因 |
|---|---|
| 左右分屏 + 左上角 `BEFORE` / `AFTER` 标签 | 顺序播放时观众会忘记上一段 |
| 每次只改**一行**，改完念出「我把 X 改成 Y」 | 观众要能跟上因果，不是看魔术 |
| 输出先滚到 `verdict` 再停 | 全屏 JSON 里观众找不到重点 |
| 录完一组立刻还原并跑一次 `git status` | 屏幕干净＝可信 |

## 收尾检查

```bash
git status --porcelain     # 必须为空
python -m pytest test/offline -q   # 230 passed
```

如果这两条不成立，**不要**继续录下一组——先还原，再重来。
