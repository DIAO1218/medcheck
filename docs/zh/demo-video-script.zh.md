# 演示视频脚本（10 分钟，可直接照录）

> 目标时长 **9:20**（上限 10:00，留 40 秒缓冲）。
> 口播：**英文**，字幕：中英双语（剪映自动字幕 + 本文件的台词文本）。
> 本文件里的所有命令与预期输出都已在仓库中实测过，日期 2026-11-23。

---

## 0. 录制前必读

### 0.1 一次性准备（5 分钟）

```bash
cd "GROUP PROJECT/MedCheck"
pip install -e ".[dev]"        # 若已装过可跳过
export PYTHONPATH=src          # 不装包时必须；装了包也可以留着，无副作用
python -m pytest test/offline -q   # 确认 230 passed
```

> 注意：`python -m medcheck.api.cli` 需要 `PYTHONPATH=src` 或 `pip install -e .`。忘记这一步，视频第一秒就会报 `ModuleNotFoundError`。

### 0.2 环境

- [ ] Windows 专注助手 → 仅闹钟；关微信 / 邮件 / OneDrive 弹窗
- [ ] 终端字号 ≥ 16pt，深色主题，窗口固定在同一位置（不要拖动）
- [ ] 断网（避免 CI 角标、通知入镜）
- [ ] 终端提示符里若含用户名，先 `cd` 进项目再 `clear`，屏幕上只留项目相对路径
- [ ] 录 15 秒试音，回放确认无爆音、无风扇声

### 0.3 录制方式（强烈建议）

**分段录屏 + 单独配音 + 剪辑对齐**，不要一镜到底。

- 录屏：OBS Studio，只捕获终端窗口（段 1、5 用幻灯片窗口）
- 配音：对着本文件的台词念，一段一录，卡壳只重录该段
- 剪辑：剪映专业版，贴画面 → 放配音 → 自动字幕 → 手动改术语

---

## 1. 分镜总表

| # | 时间码 | 画面 | 一句话目的 |
|---|---|---|---|
| 1 | 0:00–0:40 | 标题 + 一张「错批 vs 多报」对比卡 | 立住论点 |
| 2 | 0:40–2:30 | 终端：三个 case 的 JSON 输出 | 证明产品真的会拒绝 |
| 3 | 2:30–4:10 | 终端：三组前后对比（分屏） | 证明改动是承重的 |
| 4 | 4:10–5:50 | 代码：契约、结构测试、覆盖空洞 | 讲原始工程想法 |
| 5 | 5:50–7:20 | 终端 + 编辑器：可追溯、权限、提示词 | 讲治理与可追溯 |
| 6 | 7:20–8:50 | 终端：测试与门禁 + 变异实验 | 讲验证强度 |
| 7 | 8:50–9:20 | 三张「未完成」截图 | 主动交底 |

---

## 2. 逐段脚本

### 段 1｜0:00–0:40 立论

**画面**：标题卡 `MedCheck — a medication checker that refuses to answer`，下面两行对比：

```
wrong APPROVE  →  a patient is harmed
extra  HOLD    →  a reviewer spends one minute
```

**英文口播**（约 90 词）

> A wrong approval hurts a patient. An extra hold costs a reviewer one minute.
> Everything you are about to see follows from that one asymmetry.
> MedCheck reads a free-text case note and returns exactly one verdict:
> approve, hold, or block. But the interesting part is not the verdict.
> It is that the model is not allowed to produce it — and we can prove that offline,
> in eight seconds, without a network or an API key.

**中文对照**

> 一次错误的「批准」会伤到病人；一次多余的「挂起」只花复核人一分钟。接下来的一切都从这一个不对称性推出来。MedCheck 读一段自由文本病历，返回三种结论之一：批准、挂起、拦截。但重点不是结论本身，而是——模型无权产生它，而且这一点可以在离线状态下用八秒证明。

**剪辑**：标题卡 0.5 秒淡入；说到 "prove that offline" 时切终端。

---

### 段 2｜0:40–2:30 产品演示

**画面**：终端，逐条粘贴命令。每条命令输出后**停 4 秒**让人读。

```bash
python -m medcheck.api.cli --case test/fixtures/cases/c01_approve_single.json
```

预期输出（取关键字段）

```
"verdict": "APPROVE"
"findings": [{ "rule_id": "SYS-PASS-001", "code": "ALL_CHECKS_PASSED", ... }]
```

```bash
python -m medcheck.api.cli --case test/fixtures/cases/c04_block_contraindicated.json
```

```
"verdict": "BLOCK"
"findings": [{ "rule_id": "DDI-007", "code": "DDI_CONTRAINDICATED",
               "statement": "clarithromycin + simvastatin: rhabdomyolysis risk (contraindicated)" }]
```

```bash
python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json
```

```
"verdict": "HOLD"
"findings": [{ "rule_id": "SYS-RENAL-001", "code": "RENAL_DATA_MISSING", ... }]
```

**英文口播**（约 240 词）

> Three cases, three verdicts.
> The first is warfarin at five milligrams with a normal kidney function. Every check
> passes, so it is approved — and notice that the approval itself is a finding with a
> rule id, not a sentence written by a model.
> The second is simvastatin plus clarithromycin. The table marks that pair as
> contraindicated, so it is blocked, and the reason names the rule: DDI-007.
> The third is the one I want you to remember. Digoxin, 125 micrograms, and the note
> never says what the kidney function is. The system does not approve it, and it does
> not block it either.
> Blocking would mean "this dose is too high". We do not know that. What we know is
> that we cannot evaluate it. So the verdict is HOLD, and the finding says exactly
> that: renal data missing.
> That distinction is the whole design. Hold is not an error state. Hold is the
> system telling the truth about the limits of its own knowledge.

**中文对照**

> 三个病例，三种结论。第一个华法林 5mg、肾功能正常，所有检查通过；注意「通过」本身也是一条带规则编号的发现，而不是模型写的一句话。第二个是辛伐他汀 + 克拉霉素，表里标为禁忌，拦截，理由写明 DDI-007。第三个请记住：地高辛 125μg，病历没写肾功能。系统既不批准也不拦截——拦截意味着「剂量过高」，而我们并不知道；我们只知道无法评估。所以是挂起，发现条目就叫「肾功能数据缺失」。这个区分就是整个设计：挂起不是错误状态，是系统在如实说明自己知识的边界。

**剪辑**：三条命令之间不要剪断，保留真实的敲击声；把 `"verdict"` 那几行用方框或放大高亮。

---

### 段 3｜2:30–4:10 前后对比（三组，左右分屏）

三段都用「左：错误行为 / 右：现在行为」的排版。操作在**项目副本**里做（见 `demo-before-after.zh.md`），不要在真仓库里改。

| 组 | 左边（before） | 右边（after） |
|---|---|---|
| BUG-0002 | 二甲双胍 + 环丙沙星 → `APPROVE` | → `HOLD` + `COVERAGE_GAP` |
| BUG-0004 | 地高辛无 eGFR → `BLOCK`（"exceeds the G5 ceiling"） | → `HOLD` + `RENAL_DATA_MISSING` |
| BUG-0012 | 改 `contracts.py` 无 ADR → `PASS` | → `FAIL: … (gate 1)` |

**英文口播**（约 220 词）

> These three pairs are not mock-ups. Each one is a real defect from our bug diary, and
> each one can be reproduced by removing a single guard.
> On the left of the first pair, the coverage check is switched off. Metformin plus
> ciprofloxacin becomes APPROVE — because "not in the table" was silently read as
> "no interaction". That is the fail-open mistake, and it is the reason the table now
> declares unassessed pairs explicitly.
> In the middle, the old behaviour banded a missing kidney function as the most
> conservative band and then compared against it, so digoxin was blocked. Blocking was
> the safer-sounding answer and the wrong one.
> On the right, our own gate: it asked whether the ledger named an ADR, and the answer
> was yes, because the baseline ADR had been there since day one. A frozen contract was
> rewritten and all six gates went green. We fixed the gate, not the PR.
> Every one of these was found by a machine disagreeing with us — not by reading code
> carefully.

**中文对照**

> 这三组不是演示素材，是缺陷日记里的真实缺陷，每一组都能靠删掉一个守卫复现。第一组左边关掉覆盖检查，二甲双胍 + 环丙沙星变成「批准」——因为「表里没有」被悄悄读成「没有相互作用」。中间那组，旧行为把缺失的肾功能当成最保守档再比较，于是地高辛被拦截；拦截是听起来更安全、但错误的答案。右边是我们自己的门：它只问台账里有没有记 ADR，而有，因为基线 ADR 从第一天就在。于是冻结的契约被改写、六道门全绿。我们修的是门，不是 PR。这三件都是机器跟我们吵架吵出来的，不是靠仔细读代码。

---

### 段 4｜4:10–5:50 原始软件工程想法

**画面**：VS Code 依次打开三个位置，每处停留 20 秒。

| 打开 | 指出什么 |
|---|---|
| `src/medcheck/contracts.py` 的 `ExtractionRecord` | 类里**没有** `verdict` / `severity` / `dose_mg_per_day` 字段 |
| `test/offline/test_structure.py` 的 `test_no_authority_import` | `extractor` 不许导入 `adjudicator` |
| `data/rules/ddi.yaml` 的 `coverage_holes` | 表里显式写「未评估」，而不是靠「没写」推断 |

**英文口播**（约 210 词）

> None of these is a business feature. They are constraints that make a class of
> mistake impossible, and each has a test that fails when you delete it.
> First, the authority seam. The extraction contract has no field for a verdict, a
> severity, or a dose. A model cannot author one because there is nowhere to put it.
> This is not a prompt that asks the model to behave; it is a type that gives it no
> vocabulary.
> Second, the structural rule: the perception layer may not import the adjudication
> layer. If someone tried to let the extractor see the verdict, the build would fail
> before review.
> Third, the table declares its own holes. Absence of a pair means "assessed, no
> interaction". It does not mean "we never looked". Those are different claims, and
> only one of them is safe to act on.
> Together these give us a property we can state in one sentence: no output of this
> system can assert a conclusion the code did not derive.

**中文对照**

> 这些都不是业务功能，而是让某一类错误不可能发生的约束，每一条都配了「删掉就失败」的测试。第一，权威接缝：抽取契约里没有结论、严重程度、剂量这三个字段，模型想写也没地方放——这不是求它守规矩的提示词，是让它没有词汇的类型。第二，结构规则：感知层不许导入裁决层，有人想让它看见结论，构建会在评审前就失败。第三，表自己声明空洞：「没有这一对」意味着「评估过、无相互作用」，不意味着「我们从未看过」。这两句话不同，只有一句能拿来行动。合起来是一句话：这个系统的任何输出都不能断言一个代码没有推导出的结论。

---

### 段 5｜5:50–7:20 可追溯 + 智能体治理

**画面**：终端 + 编辑器交替。

```bash
python scripts/validate_requirements.py
# PASS: 25 requirements (5 invariants) validate against req-schema.json
```

```bash
python -m pytest test/offline/test_structure.py -q
# 每条测试都在 docstring 里写它验证的需求或不变量的编号
```

**画面切文件**（各停 15 秒）：

| 文件 | 一句话 |
|---|---|
| `docs/req/requirements.yaml` | 25 条需求，5 条零容忍不变量，判据必须可机检 |
| `docs/architecture/trace-matrix.md` | 需求 → 测试 → 监控，逐行对照 |
| `AGENTS.md` §3 | 可写 / 冻结路径，改冻结路径需 ADR |
| `.opencode/permissions.jsonc` | 默认无读无写，9 个人类专属面 |
| `Prompt.md` | 五阶段带门：先出计划、停下等批准，再写代码 |

**英文口播**（约 210 词）

> Traceability here is not a spreadsheet somebody maintains. It is enforced.
> Every requirement has an id. Every test's docstring must name the requirement or
> invariant it verifies, and a structural test fails the build if one does not. That is
> why the matrix cannot rot: the cheapest way to add a test is also the compliant way.
> Then the agent. The agent reads AGENTS.md first, and that file tells it what it may
> not touch. The permission model is deny-by-default: no read, no write, unless a path
> is explicitly listed. Nine surfaces are human-only — including the rules that judge
> the agent.
> The launch prompt is not "build me an app". It is: produce an execution plan with
> traceability, interface contract, scope, and test strategy — then stop and wait for a
> human. In our transcripts, thirty interventions were recorded. Six were approvals.
> The other twenty-four changed what the agent was doing.

**中文对照**

> 这里的可追溯不是靠人维护的表格，而是强制的。每条需求有编号；每个测试的 docstring 必须写它验证哪条需求或不变量，否则一条结构测试会让构建失败。这就是矩阵不会腐坏的原因：加测试最省事的写法，恰好也是合规的写法。然后是智能体：它先读 AGENTS.md，那个文件告诉它什么不能碰；权限模型默认无读无写，除非路径被显式列出；九个面只有人能改——包括评判它自己的规则。启动提示词不是「给我做个应用」，而是：先产出执行计划（可追溯性、接口契约、范围、测试策略），然后停下等人。我们的会话记录里有三十处干预，其中六处是批准，其余二十四处在改变智能体正在做的事。

---

### 段 6｜7:20–8:50 验证强度与六道门

```bash
python -m pytest test/offline -q          # 230 passed in ~8s
python scripts/eval_replay.py             # faithfulness 1.0 / relevance 1.0（25 例冻结集）
```

**画面**：六道门表格（README 第 100–105 行），逐行高亮。

```bash
python scripts/check_test_approval.py --changed src/medcheck/contracts.py
# FAIL: safety-relevant change without a new or amended ADR under docs/architecture/adr/ (gate 1)
```

**英文口播**（约 200 词）

> Six gates, all blocking: test approval, static analysis, requirements schema, semantic
> evaluation, regression, and the AI-use log. The last one is unusual — if you change
> code or a prompt without recording the session that produced it, the build fails.
> That gate caught us twice, and both times we added the record instead of loosening
> the gate.
> The gate you just saw fail is the fix for our own defect. A change to a frozen
> contract must now add or amend an ADR in the same change. Citation of an old decision
> no longer counts.
> And the invariants are not just asserted. Two of the five have been mutation-checked:
> delete the guard, and a named test goes red. The other three are recorded as debt,
> with a task sheet, rather than described as done.

**中文对照**

> 六道门，全部阻断：测试审批、静态分析、需求 schema、语义评估、回归、AI 使用日志。最后一道不常见——改了代码或提示词却没记录产出它的会话，构建就失败。这道门拦过我们两次，两次我们都补记录，而不是放松门。你刚看到失败的那道，是我们自己缺陷的修复：改冻结契约，必须在同一次改动里新增或修订 ADR，引用旧决定不再算数。而不变量也不是嘴上说说：五条里两条做过变异检验——删掉守卫，指定的测试就变红；另外三条如实记为技术债，附任务单，而不是写成「已完成」。

---

### 段 7｜8:50–9:20 诚实边界

**画面**：三张截图并排：

1. `prompts/prompt_v1.1.yaml` 的 `live_accuracy: null`
2. `docs/debt-register.md` 的 DEBT-09（三条不变量未做变异）
3. 某份 transcript 顶部的 PROVENANCE 段

**英文口播**（约 70 词）

> Three things are not done, and they are written down rather than hidden.
> The live model path has never been measured on real notes — that field is still null.
> Three of five invariants have no mutation evidence yet.
> And the transcripts are reconstructions from the build log, awaiting member
> certification.
> A safety claim is only worth the list of things you admit you have not shown.

**中文对照**

> 三件事没做完，我们写下来了而不是藏起来：在线模型路径从未用真实病历测过，那个字段还是 null；五条不变量里三条还没有变异证据；会话记录是从构建日志重构的，等成员认证。一个安全声明，值多少取决于你承认了多少没证明的事。

---

## 3. 时间不够时砍哪里

按优先级从后往前砍：

1. 段 7 缩到 15 秒（只留一句 "three things are not done, they are in the report"）
2. 段 4 砍掉第三个点（`coverage_holes`）
3. 段 6 只跑 `pytest`，不跑 `eval_replay`

**不要砍**段 2 的 HOLD 和段 3 的任何一组对比——那是评分点。

---

## 4. 字幕要点（术语统一）

| 英文 | 字幕写法 | 不要写成 |
|---|---|---|
| HOLD | HOLD（挂起） | 暂停 / 待定 |
| fail-closed | 失败关闭（宁可拒批） | 报错 |
| authority seam | 权威接缝 | 权限边界 |
| coverage gap | 覆盖缺口 | 缺失数据 |
| mutation check | 变异检验 | 突变测试 |
| gate | 阻断门 | 检查项 |

---

## 5. 交付前自查

- [ ] 导出后实际时长 ≤ 10:00
- [ ] 1080p / 30fps / H.264 MP4
- [ ] 6 条命令的输出都露脸 ≥ 3 秒
- [ ] 无个人信息（路径用户名、邮箱、GitHub 头像）
- [ ] 字幕无错别字（尤其 `eGFR`、`APPROVE`、`DEBT-09`）
- [ ] 手机上看一遍，字号仍可读
- [ ] 上传后自己完整看一遍（不要只检查首尾）
