# 合规对照表（中文版）

> 对应英文原件 `docs/compliance-matrix.md`。逐条对照 `CS5351-2026-2027-project.pdf`，只给三种状态：**符合** / **符合但有声明偏差** / **未结**（无法仅靠改文件关闭）。
> 审计时间 2026-11-14，对应注册表 rev 2、tag `s0-baseline`。

---

## 提交模型

| 要求 | 制品 | 状态 |
|---|---|---|
| 一个仓库 | <https://github.com/DIAO1218/medcheck>（13 次提交，tag `s0-baseline`） | 符合 |
| 五份带标注的智能体会话 | `transcripts/T1…T5` | 符合，带取证声明 |
| 一份过程报告 | `Report.md` + `Report.zh.md` | 符合 |
| AI 使用日志强制且最新 | `docs/ai-use-log.yaml`（5 条） | 符合 |

## D1 —— 需求（机器可读，`./docs/req/`）

| 要求 | 制品 | 状态 |
|---|---|---|
| 机器可读 PRD（YAML） | `requirements.yaml` 的 `product_context`（愿景、用户、范围内外、成功指标、非目标） | 符合（与注册表同文件，见偏差 2） |
| 合并的需求注册表（YAML） | 同文件 `requirements`（25 条） | 符合 |
| 每条含 ID / 类型 / 陈述 / 可机检判据 / 优先级 | `req-schema.json` 的 `required` + `pattern` + `minLength`，`validate_requirements.py` 交叉校验 | 符合，门 3 验证 |
| 类型覆盖功能 / 不变量 / 质量 / 性能 / 成本 / 治理 / 安全 | 8 F / 5 I / 2 Q / 2 P / 1 C / 2 S / 5 G | 符合 |
| 不变量零容忍 | schema 条件强制 `zero_tolerance: true`；交叉检查拒绝无不变量无数量判据 | 符合 |
| 非功能需求 = metric + threshold + verification | schema 对 quality/performance/cost 强制三字段 | 符合 |
| MoSCoW + 显式取舍 | `prioritisation.framework` / `tradeoff`（≥40 字符强制） | 符合 |
| 从既有系统分析得出的需求要标注来源 | `REQ-I-001` ← `SRC-ANALYSIS-01` → `docs/bug-diary.md#BUG-0002` | 符合 |
| `req-schema.json` 被 CI 用于校验 | `.github/workflows/ci.yml` 的 `schema-gate` job | 符合 |

## D2 —— 架构制品（11 件）

| # | 制品 | 文件 | 状态 |
|---|---|---|---|
| 1 | 蓝图：范围、驱动、边界、组件、权威边界、智能体流程、权限、验证策略、可观测、变更政策 | `architecture-blueprint.md` + `docs/architecture/` 镜像 | 符合（见偏差 1） |
| 2 | ADR：选定架构、备选、理由、后果、重开条件、设计过程 | `adr/001-…md` §2–§7 | 符合 |
| 2 | AI 组件分层上下文（六层） | ADR §5 | 符合 |
| 2 | 装配管线：去重 / 优先级 / 预算 / 压实 / 组装 | ADR §5 + `extractor/context.py` | 符合 |
| 2 | token 上限 + 压实阈值 | 3000 / 2400（80%）+ `test_context_assembly.py` | 符合 |
| 2 | 压实后关键约束重注入策略 | L2 逐字重注入，测试断言 | 符合 |
| 3 | 不变量登记册（陈述/来源/执行组件/验证/运行时兜底） | `invariants.md`，5 行，五列齐全 | 符合 |
| 4 | 追踪矩阵（需求→组件→测试→运行时监控） | `trace-matrix.md`，25 行 | 符合 |
| 5 | 记忆/状态设计（跨会话/中断/版本，写与读策略、归属、保留、隐私） | `memory-design.md` §1–§6 | 符合 |
| 6 | 权限模型（按角色的文件级读写、默认拒绝、逐路径白名单） | `permission-model.md` + `.opencode/permissions.jsonc` | 符合 |
| 7 | 运行时策略目录（每条降级/失败路径） | `runtime-policy-catalog.md`（P-01…P-22） | 符合 |
| 8 | 候选评估表 | `evaluation-table.md`（5 候选、权重、敏感性） | 符合 |
| 9 | 评估日志（可选） | `evaluation-logbook.md`（E-01…E-09） | 符合 |
| 10 | 风险清单（可选） | `risk-list.md`（R-01…R-12，各带复核触发） | 符合 |
| 11 | 选项台账（可选） | `option-ledger.md`（O-1…O-12，各带重开触发） | 符合 |

## D3 —— 编码治理

| 要求 | 制品 | 状态 |
|---|---|---|
| 根目录 `AGENTS.md`：构建目标、阅读顺序、代码基线、可读/可改/冻结、模块组织、集成契约、验证要求 | `AGENTS.md` §1–§8 | 符合 |
| 结构约束：一元素一模块；只扩展不替换；模块与函数引用其 ADR 与不变量；权威边界 | `structural-constraints.md`；安全关键模块头部写明 `Decision: ADR-001 … Invariants: …` | 符合 |
| MCP 工具清单（工具 + 哪个角色可调用） | `mcp-tool-manifest.md`（4 张表 + 禁止理由） | 符合 |
| `permissions.jsonc`：机器可读权限、守卫规则、执行机制 | `.opencode/permissions.jsonc` | 符合 |
| `rules.md`：常驻行为规则，人工专属 | `.opencode/rules.md`（权限模型 §5 标为人工专属） | 符合 |
| `.agent/rules.md`：抽象上限、依赖约束、测试独立性（每功能 ≥1 负向测试）、安全关键改动需 ADR + 人工批准、上下文新鲜度（≤1 冲刺） | `.agent/rules.md` §1–§6 | 符合 |

## D4 —— 验证治理

| 要求 | 制品 | 状态 |
|---|---|---|
| 每条判据 ≥1 测试 | 追踪矩阵；`test_every_requirement_is_traced` 强制 | 符合 |
| 每条不变量有「违反即失败」的测试 | `test_invariants.py`；INV-001/003 已做变异检验 | **部分符合**：3 条未做（DEBT-09） |
| 每个测试引用它验证的需求/不变量 | 136 个测试函数全部带编号；`test_every_test_declares_its_requirement` 强制 | 符合 |
| 每轮跑全部历史套件、零回归 | 门 5 全量跑 `test/offline` | 符合 |
| 三层：结构 / 回归 / 行为 | `verification-constraints.md` §2 | 符合 |
| `review-memo.md`：每 PR 覆盖规格/架构/质量/运维，含安全与效率，给出 APPROVE / CHANGES REQUIRED / REJECT | 2 份（PR #0、#1） | 符合 |
| 债务表覆盖八类 AI 时代债务 | 13 条：提示词腐坏、臆测依赖、不可触碰代码、隐藏依赖、智能体膨胀、评估债、护栏债、人的认知债 | 符合 |
| 缺陷日记：症状/复现/分类/根因/修复/暴露的不变量缺口 | 7 条，六字段齐全 | 符合 |

## D5 —— 会话记录

| 要求 | 制品 | 状态 |
|---|---|---|
| 一份完整的、从零构建实现的原始记录 | T4 | 符合，但为重构 |
| 五份带标注记录 | T1–T5 | 符合 |
| 每次干预标注 + 理由 | 30 处（REJECT 8 / REDIRECT 9 / CORRECT 4 / INTERRUPT 3 / APPROVE 6），每处含「为什么」与「改成什么」 | 符合 |
| 集体覆盖：需求分类、候选生成与评估、编码前计划审批、构建、验证合规、依测试证据修订架构 | 分别由 T1、T2、T3、T4、T4+§7、T5 覆盖 | 符合 |

## D6 —— 报告

| 要求 | 制品 | 状态 |
|---|---|---|
| 单份 markdown | `Report.md`（英文提交版）+ `Report.zh.md`（中文对照） | 符合 |
| 全体姓名与学号 | §1 映射表 | **未结**：`⟨M1⟩`–`⟨M6⟩` 占位 |
| 全队相对贡献 | §1 工时表 + 权重公式 + 算例 | 结构符合；工时**未结** |
| ≤ 10,000 词（不含图表） | 9,279 词 | 符合 |
| Point 12 单倍行距 > 15 页 | 约 18 页（~500 词/页，含 4 附录 12 表） | 符合（估算，导出 PDF 请自查） |
| 团队软件工程过程与优化 | §3、§8 | 符合 |
| 每人 300–500 词反思，含姓名学号 | §13，六段 314–384 词 | 长度符合；**语气与签名未结** |
| 过程质量证据：需求波动、缺陷趋势、歧义消解 | §9.1 / §9.2 / §9.3 | 符合 |
| 变更时制品共演化 | §10（六行传播表 + 强制机制） | 符合 |
| 人类监督抓到什么、智能体没抓到什么 | §11（三个具体案例 + 反向） | 符合 |

## D7 —— 仓库与 CI

| 要求 | 制品 | 状态 |
|---|---|---|
| 源码、测试、带阻断门的 CI/CD、分支保护、有意义的提交历史 | <https://github.com/DIAO1218/medcheck> —— 13 次提交 + tag `s0-baseline`；CI 绿（run 43474042516）；`main` 已开分支保护：需 PR、需 1 次批准、`all gates` 必须绿、管理员同样受限 | 符合 |
| README 说明阻断门设计 | `README.md` 六门表 + 理由段（中英双版） | 符合 |
| 六道阻断门 | `ci.yml` 六个 job + 汇总 job | 符合 |
| 每道门有反向自测 | `test_gates_selftest.py`、`test_requirements_schema.py` 等（REQ-G-005） | 符合 |

## D8 —— 源码与测试

| 要求 | 制品 | 状态 |
|---|---|---|
| `src/`、`test/` 含完整源码与用例 | 7 个包 + 2 个模块；离线 195、在线 3 | 符合 |
| 模块名对应架构元素 | 结构约束 §1 表 ↔ 目录；`test_component_module_mapping` 强制 | 符合 |
| 测试布局区分离线与在线 | `test/offline/`、`test/live/`（`pytestmark = live`） | 符合 |

## D9 —— 静态提示词

| 要求 | 制品 | 状态 |
|---|---|---|
| 根目录单一 `Prompt.md` | `Prompt.md` | 符合 |
| 要求先出执行计划（可追溯性、接口契约、范围边界、测试策略、步骤） | Phase 1 五节表 | 符合 |
| 编码前停下等人批准 | `PLAN APPROVED` 硬停；「沉默不是批准」 | 符合 |
| 不放任无人监督跑到底 | Phase 5 交接 + 常驻禁令 | 符合 |

## 提交格式与必需结构

| 要求 | 状态 |
|---|---|
| 按 §5 结构打包的 zip | 符合（`CS5351-MedCheck.zip`）；任何改动后需重打 |
| README：目的与架构（几段话） | 符合（中英双版各三段） |
| README：项目文件组织 | 符合（带注释的目录树） |
| README：如何跑离线 / 在线 / 全量 | 符合（三条命令 + 退出码） |
| README：含真实 GitHub 仓库地址 | <https://github.com/DIAO1218/medcheck> | 符合 |

结构核对：§5 的每条路径都存在，另有蓝图镜像、`docs/test-approvals.yaml`、`SUBMISSION-CHECKLIST.md`、`docs/compliance-matrix.md`、`data/rules/`、`scripts/`、`docs/zh/`。

---

## 未结项（改文件关不掉）

| # | 事项 | 谁做 | 为什么不能自动完成 |
|---|---|---|---|
| 1 | 六人姓名 + 学号、每冲刺工时、权重 | 团队 | 工时无法从仓库重建；编造会污染作业唯一要求诚实报告的度量 |
| 2 | 六段反思用本人语气重写并签名 | 团队 | 智能体写的反思不是反思 |
| 3 | 会话记录认证或重录 | 团队 | 它们是重构件；认证只能由当事人作出 |
| 5 | 在线抽取器准确率（`prompts/*.yaml: live_accuracy`） | 团队 | 需要 API key 与真实病历 |
| 6 | INV-002/004/005 的变异检验 | 团队 | 1 小时工作，关闭 DEBT-09 |

## 声明的偏差

1. **蓝图放在两处** —— D2 要求架构文档都在 `docs/architecture/`，§5 结构要求蓝图在根目录；两处都放，`sync_blueprint.py --check` 与结构测试保证逐字节一致。
2. **PRD 与注册表同一文件** —— 两份必须一致的 YAML 就是两份会漂移的文档；schema 对两个块都做校验。
3. **会话记录是重构件** —— 五份文件头、记录目录 README、审查备忘录、报告 §6.3 都写明。
4. **`req-schema.json` 是 JSON** —— 跟随作业给的文件名，而不是它的散文表述。
5. **工时与反思是空/占位** —— 编造的数字比空格更糟，这个项目在三处论证过这一点。
