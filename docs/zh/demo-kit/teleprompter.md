# 提词卡（照着念）

> 只含台词。每段前面是时间码与字数，念完按段落停。
> 语速参考：英文约 140 词/分钟。括号里是动作提示，不要念出来。

---

## 段 1 · 0:00–0:40（约 90 词）

（卡片 1 → 卡片 2）

A wrong approval hurts a patient.
An extra hold costs a reviewer one minute.
Everything you are about to see follows from that one asymmetry.

MedCheck reads a free-text case note and returns exactly one verdict:
approve, hold, or block.
But the interesting part is not the verdict.
It is that the model is not allowed to produce it —
and we can prove that offline, in eight seconds,
without a network or an API key.

---

## 段 2 · 0:40–2:30（约 240 词）

（卡片 3 → 切终端）

Three cases, three verdicts.

The first is warfarin at five milligrams with normal kidney function.
Every check passes, so it is approved —
and notice that the approval itself is a finding with a rule id,
not a sentence written by a model.

The second is simvastatin plus clarithromycin.
The table marks that pair as contraindicated, so it is blocked,
and the reason names the rule: DDI-007.

The third is the one I want you to remember.
Digoxin, 125 micrograms, and the note never says what the kidney function is.
The system does not approve it, and it does not block it either.

Blocking would mean “this dose is too high”. We do not know that.
What we know is that we cannot evaluate it.
So the verdict is HOLD, and the finding says exactly that: renal data missing.

That distinction is the whole design.
Hold is not an error state.
Hold is the system telling the truth about the limits of its own knowledge.

---

## 段 3 · 2:30–4:10（约 220 词）

（卡片 4 出现 BEFORE / AFTER → 分屏录屏）

These three pairs are not mock-ups.
Each one is a real defect from our bug diary,
and each one can be reproduced by removing a single guard.

On the left of the first pair, the coverage check is switched off.
Metformin plus ciprofloxacin becomes APPROVE —
because “not in the table” was silently read as “no interaction”.
That is the fail-open mistake,
and it is the reason the table now declares unassessed pairs explicitly.

In the middle, the old behaviour banded a missing kidney function
as the most conservative band and then compared against it,
so digoxin was blocked.
Blocking was the safer-sounding answer and the wrong one.

On the right, our own gate:
it asked whether the ledger named an ADR, and the answer was yes,
because the baseline ADR had been there since day one.
A frozen contract was rewritten and all six gates went green.
We fixed the gate, not the pull request.

Every one of these was found by a machine disagreeing with us —
not by reading code carefully.

---

## 段 4 · 4:10–5:50（约 210 词）

（卡片 5 → 编辑器三个位置）

None of these is a business feature.
They are constraints that make a class of mistake impossible,
and each has a test that fails when you delete it.

First, the authority seam.
The extraction contract has no field for a verdict, a severity, or a dose.
A model cannot author one because there is nowhere to put it.
This is not a prompt that asks the model to behave;
it is a type that gives it no vocabulary.

Second, the structural rule:
the perception layer may not import the adjudication layer.
If someone tried to let the extractor see the verdict,
the build would fail before review.

Third, the table declares its own holes.
Absence of a pair means “assessed, no interaction”.
It does not mean “we never looked”.
Those are different claims, and only one of them is safe to act on.

Together these give us a property we can state in one sentence:
no output of this system can assert a conclusion the code did not derive.

---

## 段 5 · 5:50–7:20（约 210 词）

（终端跑两个命令 → 切 AGENTS.md / permissions.jsonc / Prompt.md）

Traceability here is not a spreadsheet somebody maintains. It is enforced.

Every requirement has an id.
Every test's docstring must name the requirement or invariant it verifies,
and a structural test fails the build if one does not.
That is why the matrix cannot rot:
the cheapest way to add a test is also the compliant way.

Then the agent.
The agent reads AGENTS.md first,
and that file tells it what it may not touch.
The permission model is deny-by-default:
no read, no write, unless a path is explicitly listed.
Nine surfaces are human-only — including the rules that judge the agent.

The launch prompt is not “build me an app”.
It is: produce an execution plan with traceability, interface contract,
scope, and test strategy — then stop and wait for a human.

In our transcripts, thirty interventions were recorded.
Six were approvals.
The other twenty-four changed what the agent was doing.

---

## 段 6 · 7:20–8:50（约 200 词）

（终端：pytest、eval_replay、门 1 FAIL → 卡片 6）

Six gates, all blocking:
test approval, static analysis, requirements schema,
semantic evaluation, regression, and the AI-use log.

The last one is unusual —
if you change code or a prompt without recording the session that produced it,
the build fails.
That gate caught us twice, and both times we added the record
instead of loosening the gate.

The gate you just saw fail is the fix for our own defect.
A change to a frozen contract must now add or amend an ADR
in the same change.
Citation of an old decision no longer counts.

And the invariants are not just asserted.
Two of the five have been mutation-checked:
delete the guard, and a named test goes red.
The other three are recorded as debt, with a task sheet,
rather than described as done.

---

## 段 7 · 8:50–9:20（约 70 词）

（卡片 8 → 三张截图）

Three things are not done, and they are written down rather than hidden.

The live model path has never been measured on real notes —
that field is still null.

Three of five invariants have no mutation evidence yet.

And the transcripts are reconstructions from the build log,
awaiting member certification.

A safety claim is only worth the list of things you admit you have not shown.

（卡片 9）

A system that can refuse is more trustworthy than one that always answers.

---

## 念稿提示

- 每段开头**先吸一口气再出声**，剪辑时好切
- `HOLD` 念得比周围慢半拍——这是全片最重要的词
- 数字念清楚：`DDI-007`、`250`、`thirty`（不要念 thirty-one）
- 不要念文件路径（`src/medcheck/...`），念「the extraction contract」即可
- 卡住就重念**这一句**，不要整段重来（分段录音时）
