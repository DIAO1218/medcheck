# 中文对照版索引

本目录放所有中文文档，供组内与同学快速通读。**正式提交文本仍以英文原文件为准**（作业要求英文交付），中文版用于理解与讨论，两版内容与数字保持一致。

## 中文文档

| 文件 | 对应英文原件 | 用途 |
|---|---|---|
| [`../../项目简介.md`](../../项目简介.md) | — | 给同学看的项目简介：做什么、为什么这么设计、现在能做什么 |
| [`../../README.md`](../../README.md) | `README.en.md` | 项目入口（中文为主，英文版单独保留） |
| [`../../Report.zh.md`](../../Report.zh.md) | `Report.md` | 过程报告全文中文版（13 节 + 4 附录） |
| [`architecture-overview.zh.md`](architecture-overview.zh.md) | `architecture-blueprint.md` + `docs/architecture/adr/001-…md` | 架构导读：接缝、数据流、结论语义、五条不变量、六层上下文、权限、被否方案 |
| [`transcript-summaries.zh.md`](transcript-summaries.zh.md) | `transcripts/T1…T5` | 五场会话摘要，含 30 处干预的关键几条 |
| [`compliance-matrix.zh.md`](compliance-matrix.zh.md) | `docs/compliance-matrix.md` | 逐条对照作业要求，含未结项与声明偏差 |
| [`submission-checklist.zh.md`](submission-checklist.zh.md) | `SUBMISSION-CHECKLIST.md` | 提交前要跑的命令、要填的表、要背下来的七个问题 |

## 还没翻译的（按需再翻）

以下为工程文档，术语密集、改动频繁，优先保留英文以避免两版不同步：

- `docs/req/requirements.yaml`、`req-schema.json`（机器可读，字段已自解释）
- `docs/architecture/` 下除蓝图与 ADR 外的九件制品（不变量登记册、追踪矩阵、记忆设计、权限模型、运行时策略、评估表、评估日志、风险清单、选项台账）
- `docs/code-governance/` 三件（结构约束、验证约束、MCP 工具清单）
- `AGENTS.md`、`Prompt.md`（智能体读的文件，团队若用中文智能体再翻）
- `docs/bug-diary.md`、`debt-register.md`、`review-memo.md`

需要时按这个顺序翻：不变量登记册 → 追踪矩阵 → 缺陷日记。这三份承载了其他文档引用最多的术语。

## 术语对照（读英文原件时用）

| 英文 | 中文 | 说明 |
|---|---|---|
| invariant | 不变量 | 零容忍规则，一条违规即阻塞发布 |
| authority boundary | 权威边界 | 谁是「建议」、谁是「权威」的分界 |
| fail-closed | 失败关闭 / 宁可拒批 | 不确定时不是放行，而是挂起并升级 |
| coverage gap | 覆盖缺口 | 药或药对不在表内（含声明未评估） |
| ceiling | 上限（日剂量） | 按肾功能分档后的最大值 |
| renal band | 肾功能分档 | 按 eGFR 缩放上限的档位 |
| fit criterion | 判据 | 可机检的验收条件 |
| trace matrix | 追踪矩阵 | 需求 → 组件 → 测试 → 运行时监控 |
| mutation check | 变异检验 | 删掉守卫，看测试是否变红 |
| gate | 门（阻断门） | CI 里会拦下合并的检查 |
| adjudicator | 裁决器 | 合成结论的确定性模块 |
| extraction record | 抽取记录 | 模型输出的结构化结果，无权威字段 |
| advisory | 建议文案 | 给人看的散文，下游不读 |
| hold / block / approve | 挂起 / 拦截 / 批准 | 三种结论 |
| redaction / masking | 脱敏 | 标识符换成类型化令牌 |
| provenance | 取证来源 | 这份记录是现场抓取还是重构 |
| debt register | 技术债登记表 | 含八类 AI 时代债务 |
| ADR | 架构决策记录 | 决定 + 备选 + 重开条件 |

## 给同学的两句话

如果想 10 分钟看懂这个项目：先读本目录的 `architecture-overview.zh.md` §1–§5，再读 `transcript-summaries.zh.md` 的「总览」和「五场连起来说明了什么」。

如果要照着做一遍：读 `architecture-overview.zh.md` §11「如果你想动手改」，然后跑 `python -m pytest test/offline -q`，看 195 个测试是怎么把「模型不能决定任何事」这句话变成可执行检查的。
