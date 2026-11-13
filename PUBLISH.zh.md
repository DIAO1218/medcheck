# 上传到 GitHub（发布指南）

> 目标：让同学能看到这个项目。推荐 **private 仓库 + 邀请同学为 collaborator**，理由见 §0。全部步骤约 3 分钟。

---

## 0. 先决定：公开还是私有

| 选择 | 适合 | 代价 |
|---|---|---|
| **Private（推荐）** | 课程作业、组内与同学查看 | 需要逐个邀请，或用 GitHub 的 "invite by link" |
| Public | 想当作品集、答辩后展示 | 任何人可复制；仓库里含学号与姓名（`transcripts/` 文件名、`ai-use-log.yaml`） |

两条具体理由让你选 private：**(1)** 仓库里有 `60371620 DIAO Liuxianjia` 的学号与姓名，公开即公开个人标识；**(2)** 这是待评分作业，公开等于把可复制的完整答案放在搜索引擎里，同学「查看」和「抄」之间没有技术边界。

如果之后要转公开：`gh repo edit --visibility public --accept-visibility-change-consequences`。答辩结束后再做更稳妥。

## 1. 授权一次（只需一次）

在本机终端里跑：

```bash
gh auth login
```

选 `GitHub.com` → `HTTPS` → `Login with a web browser`，把终端里显示的 8 位码输进浏览器。完成后再跑 `gh auth status`，应显示 `Logged in to github.com`。

> 如果不装 gh，也可以在本机终端执行 `git push` 时按提示用浏览器登录（Git Credential Manager 会弹窗）。gh 只是让「建仓库 + 推送 + 设分支保护」变成三条命令。

## 2. 建仓库并推送

授权完成后，在 `GROUP PROJECT/MedCheck/` 下执行：

```bash
gh repo create medcheck --private --source=. --remote=origin --push
```

它会：创建 `github.com/<你的账号>/medcheck` → 加 remote `origin` → 推送 `main` 分支和 tag。

如果没有 gh，等价的网页流程是：GitHub 新建空仓库（不要勾 README/gitignore）→ 然后

```bash
git remote add origin https://github.com/<账号>/medcheck.git
git push -u origin main
git push origin s0-baseline
```

## 3. 打开分支保护（D7 要求，1 分钟）

```bash
gh api -X PUT repos/:owner/medcheck/branches/main/protection \
  -F required_status_checks.strict=true \
  -F 'required_status_checks.contexts[]=all gates' \
  -F enforce_admins=true \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F restrictions=null
```

对应作业要求：`ci` 必须通过才能合并；本仓库的汇总检查名是 `all gates`（见 `.github/workflows/ci.yml` 最后一个 job）。安全路径另需人工审查 + ADR，这一条由 `gate 6` 的 `check_test_approval.py` 在 CI 里强制（安全关键模块缺 ADR 直接失败），分支保护只负责「必须有人批过」。

## 4. 让同学能看

私有仓库两种给法：

- **逐个邀请**：`gh api repos/:owner/medcheck/collaborators/<同学GitHub用户名> -X PUT -f permission=read`
- **邀请链接**：仓库 Settings → Collaborators → 生成 invite link，发给同学（有效期 7 天，可重发）

只想给一个人看某份报告：直接把 `Report.zh.md` 或 `Report.md` 发过去更快，不必开仓库权限。

## 5. 推之前先过一遍

```bash
python -m pytest test/offline -q          # 195 passed
python scripts/validate_requirements.py    # PASS
git status --porcelain                      # 应为空
git log --oneline | head                   # 9 次提交，最新是 docs(zh)
```

如果 `git status` 不干净，先提交；`.gitignore` 已排除 `data/audit`、`data/state`、`data/cache`、`.env`、`*.key`，所以病例数据与密钥不会被推上去。

## 6. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `remote: Repository not found` | 仓库名或账号拼错；或授权的是另一个 GitHub 账号（`gh auth status` 看清是哪个） |
| 推送卡住或反复要密码 | 用 `gh auth setup-git` 让 gh 接管凭据，再 `git push` |
| CI 全红，报 `No module named medcheck` | workflow 里已用 `pip install -e ".[dev]"`；若你改过 `pyproject.toml` 的 `packages.find`，先本地跑一遍 `pip install -e .` |
| CI 门 1 红 | `docs/test-approvals.yaml` 里对应模块 `approved: false`，或改动路径推导出的模块名不在台账里 |
| 不想让 CI 跑 | 别删 workflow——D7 就靠它；把仓库设为 private 后 Actions 仍可跑，额度足够 |

## 7. 上传后的自检

```bash
gh repo view --web            # 浏览器打开确认 README 与目录
gh run list -L 3              # 看 CI 是否真的跑起来
gh api repos/:owner/medcheck/branches/main/protection | head -20   # 分支保护是否生效
```

三件事都对，才算「上传完成」：**代码在、CI 绿、分支保护开**。只做到第一条的话，D7 里「带阻断门与分支保护的仓库」仍然只算完成一半。
