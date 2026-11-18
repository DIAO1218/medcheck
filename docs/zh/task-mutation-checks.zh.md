# 任务：给三条不变量做变异检验（DEBT-09）

> 给 M4（rules / dose / audit 负责人）。做完约 1 小时。
> 目的不是「找 bug」，是回答一个问题：**我们自己写的那些守卫，删掉之后，测试真的会红吗？**
> 对应技术债：`docs/debt-register.md` 的 **DEBT-09**（五条不变量里只有两条做过这个检验）。

---

## 0. 为什么这件事必须做

`Report.md` §7.2 里有一句很难听但必须成立的话：

> 两个守卫被证明是承重的，三个只是被断言但未证。我们报比例而不是总数。

「有测试」和「这些测试会注意到」是两件事。删掉守卫跑一遍，如果测试红了 → 承重；如果全绿 → 那条不变量其实没有任何东西在守（这是重要发现，要报，不要偷偷把测试改宽）。

你负责的 rules/dose 正好是 INV-002 的守卫所在，所以这条债归你。

---

## 1. 准备（约 10 分钟）

```bash
# 有 GitHub 的话直接 clone（公开仓库）
git clone https://github.com/DIAO1218/medcheck
cd medcheck
pip install -e ".[dev]"

# 基线必须是绿的，否则先别改任何东西
python -m pytest test/offline -q
# 期望：199 passed
```

**没有 git 也行**：解压 `CS5351-MedCheck-clean.zip`，进目录后同样跑上面两条命令。
但那样还原文件要靠备份——见 §2 的红字。

---

## 2. 操作纪律（重要）

每做一次变异，只改**一行**，跑完立刻还原。

| 情况 | 还原方式 |
|---|---|
| 有 git | `git checkout -- <改过的文件>`，然后 `git status` 确认干净 |
| 没有 git | 改之前先 `copy 文件 文件.bak`，还原时 `copy 文件.bak 文件` 再删 `.bak` |

**绝对不要提交（commit）被破坏的代码。** 分支保护也会拦住你，但别试。

每次检验固定三步：

```bash
python -m pytest test/offline -q          # 1. 改之前，确认基线是绿的
# 2. 改那一行
python -m pytest test/offline -q          # 3. 看哪些测试红了，把输出抄下来
git checkout -- <改过的文件>               # 4. 还原
python -m pytest test/offline -q          # 5. 再跑一次，确认回到 199 passed
```

---

## 3. 五项检验

> 下表的「期望变红」是按代码读出来的推断，**不是实测**。你实测的结果才是证据；如果和期望不一致，以实测为准，并在记录里写明。

### 检验 1 — INV-002 天花板完整性

**守卫**：`src/medcheck/adjudicator/verdict.py:110`

```python
if abs(dose.ceiling_mg_per_day - expected) > 1e-9:
    raise CeilingAssertionError(...)
```

**怎么破坏**：把 `> 1e-9` 改成 `> 1e9`（阈值大到永远不触发）。

**期望变红**：`test_inv002_ceiling_cannot_be_raised_at_runtime`

**它守的是什么**：有人把结果里的上限偷偷改成 1000，好让 50mg 的剂量通过。

---

### 检验 2 — INV-002 不得静默超量

**守卫**：`src/medcheck/adjudicator/verdict.py:119`

```python
if over_ceiling and CODE_DOSE_CEILING not in codes:
    raise CeilingAssertionError(...)
```

**怎么破坏**：把整行 `if` 条件改成 `if False and ...`（或直接在 `if` 前加 `False and`）。

**期望变红**：`test_inv002_asserted_dose_above_ceiling_rejected`

**它守的是什么**：一个超上限的剂量被写进结果，却没有任何 `DOSE_CEILING` 发现——也就是「悄悄放行了一个过量」。

---

### 检验 3 — INV-004 脱敏失败必须拦住

**守卫**：`src/medcheck/privacy/mask.py:80` 的 `if strict:` 整块（第 80–92 行）

**怎么破坏**：把 `if strict:` 改成 `if False:`（保留缩进和整块内容，别删）。

**期望变红**：`test_masking_failure_blocks_the_call`

**它守的是什么**：一个识别不了的标识符形状，本来应该阻断调用，改完就变成「直接发出去」。

---

### 检验 4 — INV-005 发现必须有规则编号

**守卫**：`src/medcheck/contracts.py:202` 的 `Finding.__post_init__`

```python
if not self.rule_id:
    raise UnresolvableFinding(...)
if not self.table_version:
    raise UnresolvableFinding(...)
```

**怎么破坏**：把这两个 `if` 条件都改成 `if False:`。

**期望变红**：`test_inv005_missing_rule_id_aborts` 和 `test_inv005_missing_table_version_aborts`（两个）

**它守的是什么**：一条说不出依据的发现——复核人问「凭什么」时，答案为空。

---

### 检验 5 — INV-005 规则必须能在表里解析到

**守卫**：`src/medcheck/adjudicator/verdict.py` 的 `resolve()` 末尾那句 `raise UnresolvableFinding(...)`

**怎么破坏**：把最后那句 `raise` 改成 `return`（让无法解析的规则静默通过）。

**期望变红**：`test_inv005_unresolvable_rule_aborts`

**它守的是什么**：发现引用了一条表里根本不存在的规则（比如手滑写成 `DDI-999`），本来该中止，改完就变成照样输出。

---

## 4. 记录（产出）

把结果写进 **`docs/zh/mutation-results-<你的名字>.md`**，格式：

```markdown
# 变异检验结果 — <姓名> <学号> <日期>

| # | 不变量 | 破坏点 | 改之前 | 改之后 | 变红的测试 | 结论 |
|---|---|---|---|---|---|---|
| 1 | INV-002 完整性 | verdict.py:110 | 199 passed | ? failed | test_inv002_... | 承重 / 非承重 |
| ... | | | | | | |

## 原始输出（贴 pytest 的失败摘要，不要只写"失败了"）

```
（粘贴 python -m pytest test/offline -q 的尾部输出）
```

## 还原确认

每次改完都执行了 `git checkout -- <文件>`，最终 `git status` 为空、`pytest` 回到 199 passed。
```

**为什么写在 `docs/zh/` 而不是直接改主表**：`docs/code-governance/**` 是人工专属路径，任何智能体角色都不能写。你把结果交上来，由项目负责人合并进 `verification-constraints.md` §3 的主表。

---

## 5. 如果结果和期望不一致

三种情况，都不许「修测试」：

| 现象 | 说明什么 | 怎么办 |
|---|---|---|
| 一个都没红 | 那个守卫不是承重的（可能是死代码，或测试没覆盖到） | **这是重要发现**，原样记录，别改测试 |
| 红的比期望多 | 守卫被多处复用，影响面比想的大 | 记下多出来的那些测试名，说明耦合 |
| 改完测试直接报 ImportError / SyntaxError | 改坏语法了 | 还原，换一种改法（只改条件，别删缩进块） |

---

## 6. 这项任务顺带产出什么

做完之后你手上会有：

1. **DEBT-09 的偿还证据** —— 三条不变量从「断言」变成「已证」或「已证不承重」
2. **一段真实的会话材料** —— 你的操作、失败输出、还原确认，可以直接作为 D5 里属于你的那次会话（`transcripts/README.md` 的 T5 阶段正好是「依测试证据修订架构」）
3. **你自己的反思素材** —— §13 那段要写的是「我做了什么、哪一步我判断错了」，删守卫看红不红，比跑一遍绿测试有内容得多

---

## 7. 完成后发我

- `docs/zh/mutation-results-<名字>.md` 的内容（或直接贴群里）
- 一句话结论：五条检验里，几条承重、几条不承重
- 每冲刺工时

我把它并进 `verification-constraints.md` §3 主表，并在 `debt-register.md` 里把 DEBT-09 标为已偿还。
