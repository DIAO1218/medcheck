# 每个角色具体做什么

> 这份文件解决一个具体问题：有人读完了仓库，仍然不知道自己该干什么。
>
> 所以下面不写「负责 X 模块」这种话，而是写**现在打开哪个文件、改哪一行、怎么算做完**。每条都对应仓库里真实存在的产物，能验收。

---

## 0. 先花十分钟读这三份

| 顺序 | 文件 | 读完你应该知道 |
|---|---|---|
| 1 | [`../../项目简介.md`](../../项目简介.md) | 这个项目做什么、为什么模型不能拍板 |
| 2 | [`architecture-overview.zh.md`](architecture-overview.zh.md) | 五个包各自干什么、结论为什么只能由代码签发 |
| 3 | [`compliance-matrix.zh.md`](compliance-matrix.zh.md) 的「未结项」 | 九项交付物里还差什么、为什么只能由人补 |

读完再往下看自己那一节。

---

## 1. 总表

| 角色 | 姓名 / 学号 | 主要拥有的目录 | 现在第一件事 |
|---|---|---|---|
| 需求负责人 | DIAO Liuxianjia / 60371620 | `docs/req/`、`docs/architecture/trace-matrix.md`、`transcripts/T1–T5` | 认证五份会话（你是唯一逐场在场的人） |
| 架构负责人 | ZHU Guxi / 61016400 | `architecture-blueprint.md`、`docs/architecture/adr/`、`option-ledger.md`、`evaluation-table.md`、`risk-list.md`、`memory-design.md`、`runtime-policy-catalog.md` | 审 ADR-002（M3 在等你放行） |
| 构建 A | TanXinyue / 61050730 | `src/medcheck/{extractor,renderer}/`、`src/medcheck/pipeline.py`、`prompts/` | 写 ADR-002，让 PR #1 能合 |
| 构建 B | Lin Zijie / 60839860 | `src/medcheck/{rules,audit}/`、`data/rules/`、`test/offline/test_{units,ddi,dose,audit}.py` | 做五项变异检验（1 小时，关 DEBT-09） |
| 验证负责人 | LI Decheng / 61078578 | `test/`、`scripts/`、`.github/workflows/ci.yml`、`docs/code-governance/verification-constraints.md`、`docs/test-approvals.yaml`、`src/medcheck/api/permissions.py` | 复核变异结果，把三条不变量并进主表 |
| 过程负责人 | ZHANG Xinshuo / 60310811 | `Report.md`、`transcripts/`、`docs/{ai-use-log,review-memo,debt-register,bug-diary}.md`、`SUBMISSION-CHECKLIST.md` | 收六人信息、统稿、导 PDF 数页数 |

一句话记法：**需求管「要什么」，架构管「为什么这么搭」，两个构建管「代码」，验证管「凭什么信」，过程管「记录与提交」。**

---

## 2. 六张任务卡

### 2.1 需求负责人 — DIAO Liuxianjia（60371620）

**你拥有**
- `docs/req/requirements.yaml`（25 条需求、5 条不变量）、`req-schema.json`、`scripts/validate_requirements.py`
- `docs/architecture/trace-matrix.md`（需求 → 测试 → 监控的索引）
- `transcripts/` 五份会话：你是驱动者，T1–T5 全部由你开场

**现在就做**
1. **认证五份 transcript**。每份最末尾加一段：
   ```markdown
   **Certified.** I drove this session and confirm the interventions attributed to
   me are accurate, and that the provenance note (reconstruction, not live capture)
   is correct.

   - DIAO Liuxianjia, 60371620, 2026-11-__
   ```
   这是唯一只有你能做的事：另外五个人只能认证「属于自己的那几条干预」，全局准确性只有驱动者能签。
2. **填自己那行工时**（`Report.md` §1，表里已按姓名排好行，Sprint 1–5 五列）。
3. **核对 `REQ-Q-001` 的措辞**：它现在写的是「25 例冻结集」，这是我们实际做到的；如果你觉得该写成「语料规模随迭代增长，当前 25 例」，改这一句就够，别动阈值。

**做完的标志**
- `grep -c "Certified" transcripts/*.md` → 5
- `Report.md` §1 里你那一行没有 `[[ ]]`
- `python scripts/validate_requirements.py` → PASS

**别做**：不要为了「看起来完整」把 25 例改回 100 例。报告 §9.1 专门写了这件事，改回去等于自证那段反思是假的。

---

### 2.2 架构负责人 — ZHU Guxi（61016400）

**你拥有**
- `architecture-blueprint.md` 与 `docs/architecture/architecture-blueprint.md`（两份必须字节一致，改一份就要跑同步脚本）
- `docs/architecture/adr/`（ADR-001 以及即将有的 ADR-002）
- `option-ledger.md`（12 个被否方案）、`evaluation-table.md`（C1–C12 权重）、`risk-list.md`、`memory-design.md`、`runtime-policy-catalog.md`

**现在就做**
1. **审 ADR-002**。M3 提的 PR #1 改了 `src/medcheck/contracts.py`（冻结文件），门 6 现在要求同一改动里必须新增/修订 ADR。你要判断三件事：
   - 它说的「旧代码违反了哪条不变量」是否成立（应当是 INV-003：模型不能签发结论）；
   - 修在契约层而不是守卫层，是否真的是更小的改动；
   - 「什么情况下重开这个决定」写得是否可执行。
   合格就批准 PR；不合格就在 PR 上写清缺哪一条，别只说「再改改」。
2. **改蓝图要同步两份**：
   ```bash
   python scripts/sync_blueprint.py            # 根目录 → docs/architecture/
   python scripts/sync_blueprint.py --check    # 验证一致
   ```
3. **填自己那行工时**，并在 §13.2 反思里换成自己的话。

**做完的标志**
- PR #1 上有你的 review（APPROVE 或 CHANGES REQUIRED，附具体理由）
- `python scripts/sync_blueprint.py --check` → PASS
- 若 ADR-002 改了口径，`docs/architecture/invariants.md` 与 `trace-matrix.md` 同步更新

**别做**：不要在 PR 里顺手改 `src/`。架构负责人的改动如果夹带代码，评审就分不清「决定」和「实现」，而这正是 ADR-001 §8 想避免的。

---

### 2.3 构建 A — TanXinyue（61050730）

**你拥有**
- `src/medcheck/extractor/`（`heuristic.py`、`llm.py`、`context.py`）、`src/medcheck/renderer/template.py`、`src/medcheck/pipeline.py`
- `prompts/prompt_v1.0.yaml`、`prompt_v1.1.yaml`
- PR #1 的分支 `feat/m3-safety-boundaries`（你的）

**现在就做**
1. **补 `docs/architecture/adr/002-<短名>.md`**，让 PR #1 能合。长度不限，但必须回答三问：
   - 旧代码违反了哪条不变量？（INV-003：只有 `adjudicator/verdict.py` 能签发结论，而旧检查只扫顶层字段，把 verdict 藏进嵌套 dict 就能绕过）
   - 为什么修在契约层（`contracts.py` 的递归检查）而不是守卫层？
   - 什么条件下要重开这个决定？（例如：契约里出现合法的嵌套自由字段时）
   模板参考 `adr/001-…md` §8 那种「问题—决定—后果—重开条件」四段式。
2. **重跑 CI**。ADR 进 diff 之后 gate 6 才会放行；在那之前它一定红，那是门在工作。
3. **填工时 + 改写 §13.3 反思**（现在那段是我按角色写的草稿，署名是你的，话不是你的）。

**做完的标志**
- PR #1 的 `all gates` 变绿，且 diff 里能看到 ADR-002
- 若改了 `src/`，`docs/ai-use-log.yaml` 里同一 PR 有对应条目（gate 6 会查）

**可选（半天，能关掉一条债务）**：用真实病历跑一次在线抽取器，把准确率填进 `prompts/prompt_v1.1.yaml` 的 `live_accuracy`（现在是 `null`，对应 DEBT-06）。这是报告里唯一还没有数字的主张。

**别做**：不要把 `content` 当答案读。课程网关把答案放在 `reasoning_content`，`content` 是空的——这个坑已经记在 DEBT-13，别再踩一次。

---

### 2.4 构建 B — Lin Zijie（60839860）

**你拥有**
- `src/medcheck/rules/`（`loader.py`、`units.py`、`ddi.py`、`dose.py`）、`data/rules/*.yaml`（单位、40 对相互作用、剂量上限、肾功能分档）
- `src/medcheck/audit/log.py`（哈希链审计）
- 对应测试：`test/offline/test_{units,ddi,dose,audit}.py`、`test/fixtures/cases/` 下 25 例评估集

**现在就做**
1. **按 [`task-mutation-checks.zh.md`](task-mutation-checks.zh.md) 做五项变异检验**（约 1 小时）。这就是派给你的活，逐条写清了守卫在哪一行、改哪一行、期望哪个测试变红。
   结果写成 `docs/zh/mutation-results-linzijie.md`，每条包含：改了什么、pytest 输出摘要、是否变红、还原确认。
2. **把结果告诉我或验证负责人**，由他把 `docs/code-governance/verification-constraints.md` §3 的主表从「两条已证」改成「五条全部已证」，并把 DEBT-09 标为已偿还。
3. **填工时 + 改写 §13.4 反思**。

**做完的标志**
- `docs/zh/mutation-results-linzijie.md` 里有 5 条记录，每条都有真实 pytest 输出
- `git status` 干净（所有变异都还原了）、`python -m pytest test/offline -q` → 199 passed

**一条纪律**：如果删掉某个守卫、测试**没有**变红，那是发现，不是失败——说明那条不变量其实没人守。如实记下来，**不许改测试让它变绿**。

**别做**：不要手工改 `data/rules/ddi.yaml` 里的相互作用，然后忘了重跑 `python scripts/build_ddi_fixtures.py`。夹具与表不一致时门会红（`--check` 会告诉你）。

---

### 2.5 验证负责人 — LI Decheng（61078578）

**你拥有**
- `test/offline/`（199 项）、`test/live/`（3 项，需 key）、`test/fixtures/`
- `scripts/` 里全部七个检查脚本 + `.github/workflows/ci.yml`（六道门）
- `docs/code-governance/verification-constraints.md`、`docs/test-approvals.yaml`、`docs/code-governance/mcp-tool-manifest.md`
- `src/medcheck/api/permissions.py`（权限求值器）

**现在就做**
1. **复核 M4 的变异结果**：数值是否与我先前记录的一致（删覆盖率分支 → INV-001 挂 1 项；关权威字段检查 → INV-003 挂 10 项），不一致就查是谁改了守卫。
2. **合并进主表**：`verification-constraints.md` §3 把 INV-002/004/005 从「未证」改成「已证」，附测试名；`debt-register.md` 里 DEBT-09 标为 repaid 并在偿还表加一行。
3. **填工时 + 改写 §13.5 反思**（那段现在写的是「我有 165 个通过的测试」，这个细节是真的，但话要你自己说）。

**做完的标志**
- `verification-constraints.md` §3 五行全部有「已验证」的测试名
- DEBT-09 有偿还记录
- 全量检查一条命令跑通：
  ```bash
  python -m pytest test/offline -q && \
  python scripts/validate_requirements.py && \
  python scripts/eval_replay.py && \
  python scripts/check_permissions_sync.py && \
  python scripts/build_ddi_fixtures.py --check && \
  python scripts/sync_blueprint.py --check
  ```

**别做**：不要为了让 PR 过而放宽任何一条不变量测试。这个项目的全部说服力来自「门会红」；一次为了过而改测试，前面所有记录都变成装饰。

---

### 2.6 过程负责人 — ZHANG Xinshuo（60310811）

**你拥有**
- `Report.md` 与 `Report.zh.md`（两版必须同步）、`SUBMISSION-CHECKLIST.md`
- `transcripts/`（五份 + `README.md` 协议）、`docs/ai-use-log.yaml`
- `docs/review-memo.md`、`docs/debt-register.md`、`docs/bug-diary.md`
- 提交包（两个 zip）

**现在就做**
1. **收六人的工时**，填进 `Report.md` §1 与 `Report.zh.md` §1，用公式算权重，核对六个权重之和 ≈ 6.00。
   合计 = 五个冲刺列相加，不是另估一个数。
2. **导 PDF 数页数**。要求 >15 页（Point 12 单倍行距）。现在 9,623 词约 19 页，但排版会给不同结果——**现在就导一次**，别等提交前。不够就把 §13 六段各自分页，不要调字号。
3. **别人改完你统稿**：两版报告同一处说同一件事；`docs/ai-use-log.yaml` 每有一次 `src/` 或 `prompts/` 改动就要有一条记录（门 6 会拦）。

**做完的标志**
```bash
grep -n "\[\[" Report.md Report.zh.md          # 只剩工时格（填完应为空）
grep -c "Certified" transcripts/*.md            # 5
python -m pytest test/offline -q                # 199 passed
```
- 导出的 PDF > 15 页
- zip 重新打过（下面命令）

```bash
cd "GROUP PROJECT" && python - <<'PY'
import pathlib, zipfile
root = pathlib.Path("MedCheck"); out = pathlib.Path("CS5351-MedCheck-clean.zip")
skip = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(root.rglob("*")):
        if p.is_dir() or (set(p.parts) & skip):
            continue
        z.write(p, p.as_posix()); n += 1
print(n, "files")
PY
```

**别做**：不要替别人写反思，也不要因为他们拖到最后就代填工时。这两件事一旦代笔，报告里「八个缺陷零个靠读代码发现」「如实记录」的所有论点都会反过来打自己。

---

## 3. 六个人都要做的三件事

这三件无法由一个人代做，也不该由一个人做。

### 3.1 填工时

位置：`Report.md` §1 表格（约第 34 行）与 `Report.zh.md` §1。行标签已是你的姓名，只填自己那一行。

| 列 | 填什么 |
|---|---|
| Sprint 1 | 基线冲刺：需求、架构、治理、确定性内核（工作量最大的一块） |
| Sprint 2 | 在线抽取器、提示词 v1.0 → v1.1 |
| Sprint 3 | 验证深度（评估集扩容、变异检验） |
| Sprint 4 | 加固（运行时策略、对抗用例）——没开过就留空 |
| Sprint 5 | 过程证据（会话记录、报告） |
| 合计 | 五列相加，**不要另估** |
| 权重 | 合计 ÷ 六人均值，保留两位小数 |

- 算的是**有效投入时间**：读代码、开会、否决智能体、改文档都算，不是代码行数。
- 没开过的冲刺留空格，不要给没发生的事编工时。
- 接了难任务但失败，工时照算——制衡是「难任务」要在冲刺计划里点名。

### 3.2 改写自己的反思

位置：`Report.md` §13.x（你的名字在标题里）与 `Report.zh.md` 对应小节。要求 300–500 词（中文版对应篇幅）。

现在的文字是我按角色从构建记录写的**草稿**，署名是你的，话不是你的。改写的结构：

1. 我实际做了什么（引用一次具体干预，T1–T5 里有编号）
2. 我哪一步判断错了（必须有，这是唯一有信息量的部分）
3. 我从谁那里学到什么（指名道姓）

如果你的角色名义上和实际做的不一致（比如你是「构建负责人 A」但实际主要在写提示词），**就写清楚**——这比编一段不存在的经历安全，也符合这个项目反复强调的事。

### 3.3 认证会话记录

位置：`transcripts/` 五份。每份文件头有 `**Annotating:**` 一行，写着哪几个人要认领这份记录。在自己认领的每份末尾加：

```markdown
**Certified.** I have read this session and confirm that the interventions
attributed to me are accurate, and that the provenance note above (reconstruction
from the build log, not a live capture) is correct.

- 姓名, 学号, 2026-11-__
```

不能认证就**从 Annotating 里删掉自己**，并告诉过程负责人改报告 §6 的措辞。含糊过去比不做更糟。

---

## 4. 按你剩下的时间排

| 你有 | 做什么 |
|---|---|
| 30 分钟 | 填工时 + 在自己的 transcript 上签名 |
| 1 小时 | 上面 + 改写自己那段反思 |
| 半天 | 上面 + 认领一个具体任务（M3 的 ADR-002 / M4 的变异检验 / M6 的 PDF 页数） |
| 一整天 | 上面 + 在线抽取器实测（DEBT-06），把 `live_accuracy` 从 `null` 变成数字 |

---

## 5. 协作规则（免得白干）

- **不要直接推 `main`**：分支保护要求 PR + 一次批准，管理员也一样。开分支：`git checkout -b feat/<名字>-<内容>`。
- **自己不能批自己的 PR**：GitHub 的规则。所以至少要有另一个有写权限的人，或者临时把批准数设为 0（不推荐，报告里会显得像走过场）。
- **改动 `src/medcheck/{adjudicator,rules,privacy,audit}` 或 `contracts.py`**：同一 PR 里必须有 ADR 新增/修订 + 人工批准。门 6 会拦，拦下来是正常的。
- **改了 `src/` 或 `prompts/`**：同一 PR 里更新 `docs/ai-use-log.yaml`，否则门 6 红。
- **不要动 `.opencode/`、`.agent/`、`.github/workflows/`**：这三处是治理设施，改它们需要先改 ADR 并说明理由。

---

## 6. 五个真实出现过的误解

| 误解 | 事实 |
|---|---|
| 「代码是课程提供的吧？」 | 不是。课程只给了需求书 PDF 和 VHIS 的示范模式，代码是我们自己搭的。 |
| 「跑通了就等于我这部分完成了。」 | 跑通只说明基线没坏（199 项本来就全绿）。评分主体是过程证据：会话、反思、认证。 |
| 「这个作业就是找 bug 修 bug。」 | 找 bug 是副产品。要的是「谁在哪一步打断/否决/改向了智能体，为什么」。 |
| 「反思可以让文笔好的人代写。」 | 不行。代写的反思不是反思，评分看的是你自己的判断失误，不是文采。 |
| 「工时随便填个数。」 | 权重按 `工时 ÷ 均值` 缩放个人成绩。编造会同时污染别人的分数，且与报告里所有「如实记录」的论点冲突。 |

---

## 7. 卡住了找谁

| 问题 | 找 |
|---|---|
| 需求该不该加、判据怎么写 | DIAO Liuxianjia |
| 架构该不该改、ADR 怎么写 | ZHU Guxi |
| 抽取/提示词/渲染/在线调用 | TanXinyue |
| 药物表、剂量、肾功能分档、审计链 | Lin Zijie |
| 测试红了、门禁红了、CI 挂了 | LI Decheng |
| 报告、会话记录、提交包、GitHub 设置 | ZHANG Xinshuo |

**一条通用规则**：卡住超过 20 分钟就问，别自己硬扛。这个项目的记录方式是「谁在什么时候改向了什么」，问问题本身就是过程证据的一部分。
