# 现场演示大纲（15 分钟 + 5 分钟问答）

> 对应作业要求的七个必答点。每页给「一句话主张 + 证据 + 谁讲 + 时长」。
> 讲者用 M1–M6 代号（对照表在 `Report.md` §1）：M1 需求、M2 架构、M3 构建 A、M4 构建 B、M5 验证、M6 过程。
> 时间可按实际长度等比缩放：15 分钟版共 15 页，每页 ≤ 60 秒。

---

## 0. 讲之前的三个决定

| 决定 | 建议 |
|---|---|
| 谁讲 | 每人 2–3 页，**不要一个人讲完**——「个人贡献」这一项会看谁在台上 |
| 现场演示还是录屏 | 关键命令**提前录好**，现场只跑 2 条最稳的（`pytest`、一个 CLI case） |
| 失败怎么办 | 准备一句：「这条命令我们在视频 6:20 处完整跑过」，然后继续，不纠缠 |

---

## 1. 十五页

### P1 · 封面（M1，20 秒）

- 标题：**MedCheck — a medication checker that refuses to answer**
- 副标题一行：`CS5351 · 6 members · github.com/DIAO1218/medcheck`
- 底部小字：`NOT FOR CLINICAL USE`

### P2 · 问题：为什么不用「一次模型调用给结论」（M1，60 秒）

三行，一行一个硬伤：`cannot be proven` / `cannot be traced` / `cannot be regressed`。
右下角一行结论：**a wrong APPROVE harms a patient; an extra HOLD costs a minute.**

### P3 · 产品：三种结论（M1，60 秒）

一页放三个真实输出（截图，不要现场跑）：

| 例 | 输出 | 关键点 |
|---|---|---|
| 华法林 5mg，eGFR 90 | APPROVE | 批准本身也是一条带规则编号的 finding |
| 辛伐他汀 + 克拉霉素 | BLOCK | `DDI-007`，禁忌 |
| 地高辛 125μg，无 eGFR | HOLD | **我们不知道**，所以不批准 |

一句话：`HOLD is not an error state. It is the system telling the truth about its own limits.`

### P4 · ① 需求与规格（M1，60 秒）

- 25 条需求、5 条零容忍不变量；每条都有可机检判据
- **证据**：`docs/req/requirements.yaml`；schema 门曾把一条不可检验的判据打回（BUG-0001）
- 一句话：`A criterion that cannot fail is a wish. The schema gate rejects wishes.`

### P5 · ② 架构与集成（M2，75 秒）

- 图：`privacy → extractor → rules → adjudicator → audit → renderer`，模型只在 extractor 与 renderer 两个边缘
- 四个被否方案（各一句话）：单次模型调用 / 模型给建议但代码照抄 / 全规则无模型 / 检索增强做判据
- **集成案例**：PR #1 改的是冻结的 `contracts.py`，触发 ADR 要求——真实的新老代码交界

### P6 · 关键设计：权威接缝（M2 + M5，60 秒）

三层，缺一不可：

1. 契约里**没有** verdict / severity / dose 字段
2. 全仓库只有 `adjudicator/verdict.py` 能签发 APPROVE
3. 结构测试禁止 `extractor` 导入 `adjudicator`

一句话：`The model is not asked to behave. It is given no vocabulary.`

### P7 · ④ 人机交互（M3，75 秒）

- 30 处标注干预：8 否决 / 9 改向 / 4 纠正 / 3 中止 / **6 批准**
- 讲一个具体片段（T3）：计划**被否一次**，改完重提才批准
- 智能体职责：写代码、写测试、跑门；**不**决定需求优先级、不签发结论、不改治理文件
- 一句话：`Supervision is visible in the ratio: twenty-four of thirty interventions changed what the agent was doing.`

### P8 · ③ 团队协作与个人贡献（M6，60 秒）

- 六角色（需求/架构/构建 A/构建 B/验证/过程），五冲刺
- 权重 = 个人工时 ÷ 全员均值（投影 §1 表，**现场只有数字，不解释公式两遍**）
- 轮换的作用：**宣布完成的人**与**签字确认的人**不是同一个

### P9 · ⑤ 可追溯（M1 + M5，60 秒）

一条链，从左到右：

`REQ-F-004`（需求）→ `test_dose.py::test_over_limit_blocked`（测试）→ `gate 5`（CI）

- 强制手段：每个测试 docstring 必须写需求/不变量编号，由 `test_every_test_declares_its_requirement` 检查
- 一句话：`The cheapest way to add a test is also the compliant way.`

### P10 · ⑥ 代码审查与 CI（M5，75 秒）

六道门表格（README 第 100–105 行那一页），逐行一句话。重点讲两道：

- **门 1**：改安全路径必须在**本次改动**里新增/修订 ADR
- **门 6**：改代码或提示词必须更新 AI 使用日志（拦过我们两次，两次都是补记录）

审查：每个 PR 一份 `review-memo`，固定六段，末尾必须给 APPROVE / CHANGES REQUIRED / REJECT。

### P11 · ⑦ 缺陷：8 个，0 个靠读代码发现（M4，75 秒）

| 来源 | 数量 |
|---|---|
| 门禁 / 适应度函数 | 2 |
| 测试 | 5 |
| 人读别人的 PR | 1 |

讲两个：BUG-0002（覆盖缺口 → APPROVE）与 BUG-0004（缺 eGFR → BLOCK 改成 HOLD）。

### P12 · 返工的核心案例：门禁自己失效（M4 + M5，75 秒）

- 现象：冻结契约被改写、无 ADR、**六道门全绿**
- 根因：门问「台账里有没有 ADR」，`core` 自基线就挂着 ADR-001
- 修复：要求**本次**新增/修订 ADR；把 PR #1 的形状写成失败自测
- 一句话：`We fixed the gate, not the pull request.`

### P13 · 过程改进：我们改变了什么（M6，45 秒）

三条，都是「改变了做法」而不是「学到了很多」：

1. 缺陷日记与评估日志**当天写**（周会形式失败过一次）
2. ADR **追加**修订而不到改写原文（读者要能看见我们曾经相信过更弱的东西）
3. 门禁失败时先问「门对不对」，再问「改动对不对」

### P14 · 诚实边界（M5，45 秒）

- `live_accuracy: null`（DEBT-06）
- 五条不变量，三条未做变异检验（DEBT-09，任务单已写好）
- transcript 是重构记录，需成员认证
- 一句话：`A safety claim is worth what its list of unproven things is worth.`

### P15 · 收尾（M1，20 秒）

一句话 + 仓库二维码/链接：
`A system that can refuse is more trustworthy than one that always answers.`

---

## 2. 时间分配（15 分钟）

| 讲者 | 页 | 时长 |
|---|---|---|
| M1 | P1–P4, P15 | 3:20 |
| M2 | P5–P6 | 2:15 |
| M3 | P7 | 1:15 |
| M4 | P11–P12 | 2:30 |
| M5 | P10, P14（并协讲 P6/P9） | 2:00 |
| M6 | P8, P13 | 1:45 |
| 缓冲 | — | 1:00 |

---

## 3. 问答准备

按被问概率排序。每题给「一句话答案 + 展开一句」。

| # | 问题 | 一句话答案 |
|---|---|---|
| 1 | 你们怎么保证模型不会给出结论？ | 三层：契约无字段、单一签发点、结构测试禁止跨层导入；违反任一层，构建先失败 |
| 2 | `live_accuracy` 是 null，那你们怎么知道它能用？ | 我们不知道——所以写 null 而不是写一个好看的数；这是 DEBT-06，缺 key 与真实病历 |
| 3 | 18 个药是不是太少了？ | 规模不是论点。不变量、门禁、变异检验与表的大小无关；表小是为了每一条都能被人审 |
| 4 | 覆盖缺口率很高时怎么办？ | 监控缺口率，>20% 触发补表冲刺；**不是**放宽结论策略 |
| 5 | 分支保护真的起作用了吗？ | 起作用了，而且抓到了我们自己：PR #1 就是靠人读文件列表发现的（BUG-0012） |
| 6 | AI 写了大部分代码，你们做了什么？ | 30 处干预 24 处是改向/否决；缺陷 8 个全部由机器或他人审查发现 |
| 7 | 三条不变量没做变异检验，算验证过吗？ | 不算。记为 DEBT-09，任务单在 `docs/zh/task-mutation-checks.zh.md` |
| 8 | 为什么不用现成的药物数据库？ | 教学数据需要可审计、可版本化、许可清晰；规模不是目标，可证明性才是 |
| 9 | HOLD 太多会不会让医生不信任？ | 这是产品问题不是安全问题：错批不可逆，多挂起可恢复；缺口率是可见指标 |
| 10 | 如果模型抽错了药名怎么办？ | 抽取是感知层，错了会进入规则检查；因此每条结论都带表格版本与规则编号，可复核 |

---

## 4. 现场演示（若允许操作）

只跑两条，其余用截图：

```bash
python -m pytest test/offline -q          # 250 passed
python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json
```

第二条选 HOLD 而不是 BLOCK——它是最能说明设计意图的一条。

---

## 5. 上台前 10 分钟检查

- [ ] 投影分辨率下正文 ≥ 24pt，代码 ≥ 18pt
- [ ] 每页都有页码（问答时方便说「回到第 6 页」）
- [ ] 视频备份在本地与云端各一份
- [ ] 演示终端字体调到最大，`git status` 干净
- [ ] 每人只讲自己的页，交接时说一句「交给 M2」而不是沉默换人
