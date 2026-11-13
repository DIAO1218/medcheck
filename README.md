# MedCheck

**带确定性安全内核的用药相互作用与日剂量核查系统**
*CS5351 智能体软件工程课程项目 · 禁止用于临床*

English: [README.en.md](README.en.md) · 中文对照版索引: [docs/zh/README.md](docs/zh/README.md)

MedCheck 读取一段自由文本的病例记录，返回一份可复核的裁决：结论（`APPROVE` / `HOLD` / `BLOCK`）、按严重程度排序且每条都标注规则来源的发现列表，以及一段给复核人看的简短建议。这是教学产物，不是临床软件——每一处输出都写着这句话。

## 目的与架构（三段话）

**接缝在哪。** 语言模型负责读病历，确定性代码负责做判断。模型把散文映射成经过 schema 校验的 `ExtractionRecord`，它看不到规则表、不会输出结论、不会计算剂量。所有真正会出错的判断——单位换算、相互作用查询、日剂量上限比较、覆盖度核算、结论合成——都是查表或比较，因此同一输入加同一张表版本，输出逐字节相同。模型在出口处重新出现，只做受约束的改写，而且下游没有任何代码读取它的输出。

**为什么要有这道接缝。** 最要命的失败是"自信地错批一个 `APPROVE`"；多报一个 `HOLD` 只是让复核人多看一分钟。端到端让模型出结论的方案，无法离线证明、无法追溯到具体规则、无法脱离模型做回归测试——课程要求的三件事（可验证、可追溯、可复现）就都变成了愿望。接缝用三层强制：抽取契约里**没有**结论字段；全仓库只有一个模块可以写 `Verdict.APPROVE`；一旦感知层 import 了判决策，架构适应度函数就让构建失败。详见 `docs/architecture/adr/001-deterministic-core-model-at-the-edges.md`。

**宁可拒批，而且看得见。** 只要某个药、或某一对药不在钉住的规则表覆盖范围内——包括表里**明确声明「尚未评估」**的组合——结论就不可能是 `APPROVE`，而是带 `COVERAGE_GAP` 的 `HOLD`。缺口率是一个被监控的信号：一旦超过 20%，动作是补表覆盖，**绝不是**放宽结论策略。这个设计偏好很明确：宁可给复核人一条待读的队列，也不要给一条没人看的自动放行流水线。

## 项目结构

```
.
├── README.md                     本文件（中文）
├── README.en.md                  英文版（提交用）
├── AGENTS.md                     编码智能体的入口：阅读顺序、边界、硬性停止条件
├── architecture-blueprint.md     架构总纲 / 主约束文档（D2.1）
├── Prompt.md                     静态启动提示词，五阶段带门（D9）
├── Report.md                     过程报告 + 反思（D6，英文提交版）
├── Report.zh.md                  过程报告中文对照版（D6）
├── SUBMISSION-CHECKLIST.md       只有团队能做的事（英文）
├── docs/
│   ├── zh/                       全部中文对照版 + 中文索引
│   ├── req/
│   │   ├── requirements.yaml     25 条需求 / 5 条不变量 / PRD 块 / MoSCoW（D1）
│   │   └── req-schema.json       CI 校验用的 schema（D1）
│   ├── architecture/             ADR、不变量登记册、追踪矩阵、记忆设计、权限模型、
│   │                             运行时策略目录、候选评估表 + 评估日志、
│   │                             风险清单、选项台账、架构蓝图镜像（D2）
│   ├── code-governance/          结构约束、验证约束、MCP 工具清单（D3、D4）
│   ├── compliance-matrix.md      逐条对照作业要求（中文版在 docs/zh/）
│   ├── ai-use-log.yaml           强制维护；门 6 会拦下未更新的代码/提示词改动
│   ├── test-approvals.yaml       测试审批台账（门 1 / 门 6）
│   ├── review-memo.md            每个 PR 的审查记录（D4）
│   ├── debt-register.md          按 AI 时代分类的技术债（D4）
│   └── bug-diary.md              7 个真实缺陷 + 各自暴露的不变量缺口（D4）
├── .opencode/                    permissions.jsonc（机器可读）+ rules.md（人工专属）
├── .agent/rules.md               项目契约（人工专属）
├── .github/workflows/ci.yml      六道阻断门（D7）
├── prompts/                      prompt_v1.0.yaml、prompt_v1.1.yaml
├── src/medcheck/
│   ├── contracts.py              冻结的边界类型
│   ├── pipeline.py               唯一把各阶段串起来的地方（顺序是规范）
│   ├── privacy/                  mask / unmask / scrub              （INV-004）
│   ├── extractor/                heuristic、llm、context            （感知层）
│   ├── rules/                    units、ddi、dose、loader           （权威层）
│   ├── adjudicator/              verdict、coverage、guard           （权威层）
│   ├── renderer/                 template                           （建议，终端汇点）
│   ├── audit/                    只追加、哈希链                     （REQ-F-007）
│   └── api/                      cli、permissions
├── data/rules/                   units.yaml、ddi.yaml、dose.yaml（仅人工可写）
├── scripts/                      validate_requirements、check_ai_use_log、
│                                 check_test_approval、check_permissions_sync、
│                                 eval_replay、build_ddi_fixtures、sync_blueprint
├── test/offline/                 195 项确定性测试，无网络、无模型
├── test/live/                    依赖模型，打 `live` 标记，不进 CI 门 5
└── transcripts/                  T1–T5 五份带标注的智能体会话（D5）
```

## 跑测试

```bash
pip install -e ".[dev]"          # pyyaml + pytest + jsonschema

# 离线套件：确定性、无模型、无网络（CI 门 5 跑的就是它）
python -m pytest test/offline -q

# 在线套件：需要模型端点；未配置时自动跳过
export MEDCHECK_LLM_BASE_URL="https://<gateway>/v1"
export MEDCHECK_LLM_API_KEY="<key>"
python -m pytest test/live -q

# 全量（在线测试在无凭据时自动跳过）
python -m pytest -q
```

跑一次产品：

```bash
python -m medcheck.api.cli --case test/fixtures/cases/c04_block_contraindicated.json --advisory
python -m medcheck.api.cli --case test/fixtures/cases/c01_approve_single.json --audit data/audit/audit.jsonl
```

退出码：`0` 已裁决 · `2` 输入格式错误 · `3` 不变量中止 / 表非法 · `4` 审计不可用（结果被有意扣下不发）

## 六道阻断门

| # | 门 | 脚本 / CI job | 什么情况下拦下 |
|---|---|---|---|
| 1 | 测试审批 | `scripts/check_test_approval.py` | 改动的模块没有已审批的测试记录（安全关键模块还要求 ADR） |
| 2 | 静态分析 | `ruff`、`compileall`、结构测试、权限同步 | lint / 编译 / 跨层 import / 权限漂移 |
| 3 | Schema | `scripts/validate_requirements.py` | 需求注册表违反 schema 或跨字段规则 |
| 4 | 语义评估 | `scripts/eval_replay.py` | faithfulness < 0.90 或 relevance < 0.85 |
| 5 | 回归 | `pytest test/offline` | 任何历史测试失败，或某条不变量套件出现非零违规 |
| 6 | AI 使用日志 | `scripts/check_ai_use_log.py` | 改了 `src/` 或 `prompts/` 却没更新 `docs/ai-use-log.yaml` |

**分支保护：** `ci` 必须通过；改动 `src/medcheck/{adjudicator,rules,privacy,audit}`、`data/rules/`、`.opencode/`、`.agent/` 时，还要求人工审查且在 PR 描述里写 ADR 编号。门 1 在 S0 收尾评审之前一直是红的——因为基线是一次性写完的，不存在「实现前的审批」；`docs/test-approvals.yaml` 现在记录的是那次追溯审批，审查备忘录里写明了为什么这件事要留着给人看，而不是抹平。

## 先看哪里

| 你想…… | 去读 |
|---|---|
| 逐条核对是否符合作业要求 | `docs/compliance-matrix.md`（中文版：`docs/zh/compliance-matrix.zh.md`） |
| 知道只有团队能做什么 | `SUBMISSION-CHECKLIST.md`（中文版：`docs/zh/submission-checklist.zh.md`） |
| 看那个「其他一切决定都从它推出来」的决定 | `docs/architecture/adr/001-…md`（中文导读：`docs/zh/architecture-overview.zh.md`） |
| 看哪里坏过、是谁发现的 | `docs/bug-diary.md`（7 个缺陷，**0 个靠读代码发现**） |
| 看智能体是怎么被监督的 | `transcripts/`（30 处标注干预，中文摘要：`docs/zh/transcript-summaries.zh.md`） |

## 诚实的完成度

| 交付物 | 状态 |
|---|---|
| D1 需求 + schema | 完成，门 3 校验通过（rev 2） |
| D2 架构制品（11 件） | 完成（蓝图按必需结构放在根目录，同时在 `docs/architecture/` 有逐字节镜像） |
| D3 编码治理 | 完成 |
| D4 验证治理 | 完成；审查备忘录 #0 = CHANGES REQUIRED，#1 = APPROVE |
| D5 五份标注会话 | 已记录 T1–T5，共 30 处标注干预；每份文件开头写明取证来源 |
| D6 报告 | 内容完成（英文 9,279 词 / 约 18 页；中文对照版在 `Report.zh.md`）；姓名、工时、个人反思需本人填写（`⟨M1⟩`–`⟨M6⟩`） |
| D7 仓库 + 六道门 | 完成，门自身也被反向测试过 |
| D8 源码 + 测试 | 确定性内核完成，195 项离线测试全绿；在线抽取器已接线但尚未实测 |
| D9 静态提示词 | 完成 |

五份会话记录是根据构建日志**重构**的：智能体输出逐字引用，人的回合由已记录的决策压缩而来。每个文件开头都写明这一点；团队必须逐份认证或重新录制（见 `transcripts/README.md`）。因此，绿色套件是对确定性内核的证据，而会话记录只有在被认证之后才是对「人工监督」的证据。

## 值得争论的设计决定

- [ADR-001](docs/architecture/adr/001-deterministic-core-model-at-the-edges.md) — 接缝在哪，以及五个会让这个决定重开的条件。
- [候选评估表](docs/architecture/evaluation-table.md) — 为什么在「保留可证明性」的所有权重下，所选架构都赢；以及唯一一种它会输的权重。
- [选项台账](docs/architecture/option-ledger.md) — 十二个被否掉的选项，以及每个被重新考虑时的触发条件。
- [缺陷日记](docs/bug-diary.md) — 七个由「制品之间互相矛盾」发现的缺陷，而非读代码发现。

---

**仓库：** `<https://github.com/<org>/medcheck>` —— 提交前替换为真实 GitHub 地址（提交格式要求）。
