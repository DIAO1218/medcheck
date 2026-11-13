# 提交前检查清单（中文版）

> 对应英文原件 `SUBMISSION-CHECKLIST.md`。本仓库里的东西只有两种状态：**已完成并验证**，或**列在这里等你做**。没有中间状态——空格是诚实的，编造不是。

打包之前把 §1 的命令全跑一遍，大约 15 秒，它是「一份提交」和「一个声明」的区别。

---

## 1. 提交前验证

```bash
pip install -e ".[dev]"

python scripts/validate_requirements.py          # 门 3
python -m pytest test/offline -q                 # 门 2 + 5  → 期望 195 passed
python scripts/eval_replay.py                    # 门 4      → 期望 25 cases, 1.0 / 1.0
python scripts/check_permissions_sync.py         # 门 2
python scripts/sync_blueprint.py --check         # 蓝图两处一致
python scripts/build_ddi_fixtures.py --check     # 夹具不是旧的
python scripts/check_test_approval.py --changed src/medcheck/rules/dose.py   # 门 1 + 6
python scripts/check_ai_use_log.py --changed src/medcheck/rules/dose.py docs/ai-use-log.yaml
```

八条都必须打印 `PASS`。如果有一条失败，那个失败是真的——不要去改检查。

## 1b. 仓库已经发布

<https://github.com/DIAO1218/medcheck> 已公开，CI 绿，`main` 已开分支保护（需 PR + 一次批准 + `all gates`）。后续推送：`git push origin main`。若你的网络连不上 `github.com`，见 `PUBLISH.zh.md` §6。

## 2. 填六个人的身份（只有你们能做）

| 位置 | 填什么 |
|---|---|
| `Report.md` §1 与 `Report.zh.md` §1 | ⟨M1⟩–⟨M6⟩ 的真实姓名 + 学号 |
| 两版报告 §1 工时表 | 每冲刺实际工时，然后用公式算权重 |
| 两版报告 §13 | 每人用自己语气重写反思并签名 |
| `transcripts/*.md` 文件头 | 「Annotating」行的 ⟨M1⟩–⟨M6⟩ 换成真实姓名 |
| `docs/test-approvals.yaml` | `approved_by` 换成真实姓名 |
| `README.md` / `README.en.md` 末尾 | 真实 GitHub 地址 |

**不要编造工时。** 权重公式要除以均值；编造的输入会产出一个看起来权威的分布。由你诚实填写的空格，比一个可信的数字更值钱。

## 3. 认证会话记录，或者重录

`transcripts/` 里的五份是**重构**，依据构建日志：智能体输出逐字引用，人的回合由已记录决策压缩。每份文件头都写明。

D5 要的是带标注干预的**录制**会话。两条诚实的路：

- **（a）认证。** 逐份读，确认属于你的干预准确，然后在文件末尾加一行签名：`Certified: <姓名>, <学号>, <日期>`。然后在两版报告 §6.3 说明这是「已认证的重构」。
- **（b）重录。** 按 `transcripts/README.md` 定义的五个阶段现场跑一遍，作为新文件追加。这更强，大约花掉一天。

把（a）当成现场抓取提交属于学术不端。报告目前写明了是哪一种，请保持。

## 4. 可选但价值高（按优先级）

| # | 任务 | 为什么重要 | 工时 |
|---|---|---|---|
| 1 | 用 20 份真实感病历实测在线抽取器，填 `prompts/*.yaml: live_accuracy` | 报告里唯一还是 `null` 的主张（DEBT-06） | 半天 |
| 2 | 给 INV-002 / 004 / 005 做变异检验，记进 `verification-constraints.md` §3 | 把「5 条不变量」变成「5 条已证」（DEBT-09） | 1 小时 |
| 3 | 对 25 例做 20% 人工抽检，记录分歧率 | 让语义分数从代理指标变成有意义的度量（DEBT-01） | 2 小时 |
| 4 | 补 10 个生成式多药组合用例 | APPROVE 家族覆盖不足（DEBT-11） | 2 小时 |

只能做一件就做第 1 件：一个被测量的数字，是「我们建成了」与「我们知道它能用」之间的差别。

## 5. 打包

```bash
cd "GROUP PROJECT"
zip -r CS5351-MedCheck.zip MedCheck -x "MedCheck/.pytest_cache/*" -x "*/__pycache__/*" -x "MedCheck/data/audit/*"
```

必需结构会保留在 zip 内（`docs/req/`、`docs/architecture/`、`docs/code-governance/`、`src/`、`test/offline`、`test/live`、`transcripts/`、`.opencode/`、`.agent/`、`.github/workflows/`）。

zip 里也包含 `.git/`（9 次提交、tag `s0-baseline`），这样提交历史跟着提交件走——D7 要「有意义的提交历史」，只收到 zip 的评阅人否则看不到。如果你们老师偏好干净压缩包，可以删掉 `.git/`；但**如果还没推到 GitHub，请保留**。

## 6. 提交前老师会问的问题

提交前把这七条念出声回答一遍；哪条答得「呃」，就回去改制品，别背答案。

1. **给我看一条删掉守卫就会失败的不变量。** → INV-001 或 INV-003，两条都做过变异检验。
2. **模型决定了什么？** → 什么都没决定。它抽取字段、改写发现；结论、严重程度、剂量都来自确定性代码。
3. **药不在你们表里会怎样？** → `HOLD` + `COVERAGE_GAP`，永远不会 `APPROVE`，包括你们声明为「未评估」的组合。
4. **缺 eGFR 为什么是 HOLD 而不是 BLOCK？** → 因为 BLOCK 断言「剂量太高」，而我们不知道；HOLD 断言「我们不知道」。
5. **哪个测试在 bug 存在时会通过？** → 就是现在的 `test_inv001_unknown_drug_is_not_approved`；它在修复前写、修复前失败。
6. **有什么是人抓到而智能体没抓到的？** → §11，三个具体案例。这题不许用泛泛而谈回答。
7. **这个项目诚实的缺口在哪？** → 在线抽取器未实测；三条守卫未做变异检验；会话记录是重构件；贡献工时是占位符。四条都要主动说出来。

## 7. 九项交付物状态

| # | 交付物 | 状态 |
|---|---|---|
| D1 | 需求 + schema | 完成，门 3 验证（rev 2） |
| D2 | 11 件架构制品 | 完成 |
| D3 | 编码治理 | 完成 |
| D4 | 验证治理 | 完成（审查备忘录 #0、#1） |
| D5 | 五份标注会话 | 已记录 —— **需认证或重录** |
| D6 | 报告 | 内容完成 —— **需姓名、工时、反思** |
| D7 | 仓库 + 六道门 | 完成，门自身做过反向测试 |
| D8 | 源码 + 测试 | 完成（离线 195、在线 3 带标记） |
| D9 | 静态提示词 | 完成 |

有两个格子还得靠你们，而且它们在报告里也被标出来了。这是预期状态：必须由团队亲自拥有的制品，正是那些关于团队的制品。
