# 开工清单（现在就能开录）

> 目标：今晚录完素材，明天剪。全程不需要装软件（Windows 自带 `Win+G` 录屏）。
> 配套文件：`cards.html`（卡片）、`teleprompter.md`（台词）、`../demo-before-after.zh.md`（前后对比复现）。

---

## 第 0 步 · 10 分钟环境设置（只做一次）

- [ ] 显示缩放设为 **100%**，分辨率 **1920×1080**（录屏清晰度靠这个）
- [ ] 打开「专注助手」→ 仅闹钟；退出微信 / QQ / 邮件
- [ ] 终端：字号调到 **18–20**，深色主题，窗口最大化
- [ ] 浏览器打开 `docs/zh/demo-kit/cards.html`，按 `F` 全屏，`→` 试翻两页
- [ ] 关闭输入法（`Shift` 切英文），否则命令里会出现中文标点

**终端准备（每段开录前都做）**

```bash
cd "C:/Users/26657/Desktop/CS5351/GROUP PROJECT/MedCheck"
export PYTHONPATH="$(cygpath -w "$PWD/src")"
clear
```

> 记住这条：`PYTHONPATH` 必须是 **Windows 路径**，用 `cygpath -w` 转。否则 `python -m medcheck...` 会报 `ModuleNotFoundError`。

---

## 第 1 步 · 录屏（7 段，约 25 分钟）

### 快捷键

| 操作 | 键 |
|---|---|
| 开始 / 停止录制 | `Win + Alt + R` |
| 打开录屏面板 | `Win + G` |
| 录制文件位置 | `此电脑 → 视频 → 捕获` |

**每段流程（照做，不要即兴）**

1. 切到目标窗口 → 静置 2 秒
2. `Win + Alt + R` 开始
3. 默数 2 秒再动手（剪辑时要留手）
4. 按该段清单操作（**不用念台词**，配音后面单独录）
5. 停手 → 默数 2 秒 → `Win + Alt + R` 停止
6. 文件重命名为 `seg1` … `seg7`

### 各段屏幕准备

| 段 | 屏幕内容 | 操作要点 |
|---|---|---|
| **1** | `cards.html` 第 1 页 | 静止 8 秒；`→` 到第 2 页，静止 12 秒 |
| **2** | 终端 | 依次粘贴 3 条命令，每条输出后停 **4 秒**；滚动到能看到 `"verdict"` |
| **3** | 两个终端并排 + 卡片 4 | 见下方「分屏怎么录」 |
| **4** | 编辑器 | 依次打开 `contracts.py`（滚到 `ExtractionRecord`）、`test_structure.py`（`test_no_authority_import`）、`ddi.yaml`（`coverage_holes`），每处停 15 秒，鼠标指着那几行 |
| **5** | 终端 → 编辑器 | 跑 2 条命令 → 依次打开 `AGENTS.md`、`permissions.jsonc`、`Prompt.md`，各停 12 秒 |
| **6** | 终端 | 跑 `pytest`、`eval_replay`、门 1 FAIL；最后切卡片 6，静止 10 秒 |
| **7** | 卡片 8 → 三张截图 | 截图：`prompt_v1.1.yaml` 的 `live_accuracy: null`、`debt-register.md` 的 DEBT-09、任一份 transcript 的 PROVENANCE 段 |

### 段 2 的三条命令（直接粘贴）

```bash
python -m medcheck.api.cli --case test/fixtures/cases/c01_approve_single.json
python -m medcheck.api.cli --case test/fixtures/cases/c04_block_contraindicated.json
python -m medcheck.api.cli --case test/fixtures/cases/c11_hold_missing_egfr_renal.json
```

### 段 6 的三条命令

```bash
python -m pytest test/offline -q
python scripts/eval_replay.py
python scripts/check_test_approval.py --changed src/medcheck/contracts.py
```

第三条**预期失败**（退出码 1），画面出现 `FAIL: … (gate 1)` 就对了。

### 分屏怎么录（段 3）

不需要真的分屏，两步更省事：

1. **先录 AFTER**：真仓库里跑三个 case，各停 3 秒（这就是"现在"）
2. **再录 BEFORE**：按 `../demo-before-after.zh.md` 在副本里改一行，再跑同样三个 case
3. 剪辑时把 BEFORE 放左、AFTER 放右，加 `cards.html` 第 4 页做 1 秒转场

> 副本位置建议：`cp -r MedCheck /tmp/mcdemo`（连 `.git` 一起复制，还原用 `git checkout -- <文件>`）。

---

## 第 2 步 · 配音（约 20 分钟）

- [ ] 安静房间，手机录音机或 Audacity，离麦 15 cm
- [ ] 打开 `teleprompter.md`，**一段一条**，命名 `vo1` … `vo7`
- [ ] 每条开头留 1 秒静音（对齐时好用）
- [ ] 念错就停 2 秒重念该句，剪辑时剪掉坏的
- [ ] 录完回放：有没有喷麦、有没有空调声

**语速参考**：段 2 约 240 词，应在 1 分 45 秒内念完；超了就说明念慢了，整段会顶到 10 分钟。

---

## 第 3 步 · 剪辑（剪映，约 40 分钟）

1. 新建项目：**16:9，1920×1080，30fps**
2. 导入 7 段录屏 + 7 段配音
3. 按时间码摆画面：`0:00 / 0:40 / 2:30 / 4:10 / 5:50 / 7:20 / 8:50`
4. 每段画面按配音长度裁剪（画面可以比声音长，反之不行）
5. 卡片段：直接用 `cards.html` 的录屏，或用截图放大
6. 自动字幕 → 逐条改术语（HOLD 不是「保持」，gate 不是「大门」）
7. 统一响度：剪映「响度统一」，目标 −14 LUFS
8. 导出：1080p / 30fps / H.264 / MP4

---

## 第 4 步 · 交付前 6 条检查

- [ ] 实际时长 ≤ 10:00（看导出后的时长，不是时间轴）
- [ ] 每条命令的输出都露脸 ≥ 3 秒
- [ ] 没有个人信息：路径里的用户名、邮箱通知、GitHub 头像
- [ ] 字幕无错：`eGFR`、`APPROVE`、`DEBT-09`、`DDI-007`
- [ ] 手机上看一遍，字号还能读
- [ ] 上传后从头看一遍（不要只检查首尾）

---

## 如果只有 45 分钟

砍到 3 段，其余用卡片 + 配音撑：

| 保留 | 时长 | 为什么不能砍 |
|---|---|---|
| 段 2 产品演示 | 1:50 | 证明系统真的会拒绝 |
| 段 3 前后对比 | 1:40 | 证明改动是承重的 |
| 段 6 门禁 | 1:30 | 证明验证不是嘴上说的 |

其余段落：卡片静止 + 配音，剪成 5 分钟版本也能交，但会明显薄——**优先保证这三段是真实录屏**。

---

## 出问题时

| 现象 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: medcheck` | `PYTHONPATH` 不是 Windows 路径 | 重新执行 `export PYTHONPATH="$(cygpath -w "$PWD/src")"` |
| 录出来只有一半屏幕 | `Win+G` 录的是「当前窗口」 | 先点一下目标窗口再开始录 |
| 命令里出现中文标点 | 输入法没关 | `Shift` 切英文；或直接右键粘贴 |
| 录到的画面发虚 | 显示缩放不是 100% | 设置 → 显示 → 缩放 100% |
| 配音和画面对不上 | 先剪画面再配音 | 顺序反了，按「画面 → 配音 → 字幕」重来 |
