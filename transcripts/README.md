# Transcripts — D5

`[[This directory holds the five annotated agent sessions. It currently holds the protocol, not the evidence.]]`

D5 asks for one full, raw transcript per session showing the supervised pipeline end to end, annotated with the team's interventions and a rationale for each. This README defines how to record them so that the set is coherent rather than five unrelated chat logs.

## Naming

```
transcripts/<student-id>-<student-name>.md
```

Example: `transcripts/60371620-DIAO-Liuxianjia.md`. One file per student, containing that student's sessions in order. If a session is run by two people, the driver owns the file and the other annotates inline with their initials.

## The five sessions (collectively they must show the whole pipeline)

| # | Session | Must show | Gate in `Prompt.md` |
|---|---|---|---|
| T1 | Requirements classification | the agent proposing a requirement split, a human reclassifying one as invariant, a fit criterion rejected as unfalsifiable and rewritten | Phase 0 |
| T2 | Architecture candidate generation and evaluation | ≥2 candidates scored, a human challenging a score, the evaluation table changed as a result | Phase 1 |
| T3 | Plan approval before code | a full execution plan (traceability, interface contract, scope, tests, steps), a human rejecting it once, then `PLAN APPROVED` | Phase 1 → 2 |
| T4 | Build and verification | tests written first and failing, implementation, raw gate output pasted, one test that had to be corrected because it asserted the wrong thing | Phase 2 → 4 |
| T5 | Architecture revision from test evidence | a test that contradicted the design, an ADR amendment drafted, the invariant restated | Phase 4 → 5 |

Sessions may be split across students, but the five must exist and must be **contiguous in the record**: the plan in T3 must be the plan T4 implements.

## Annotation format

Interventions are marked inline, at the point they happened, with the reasoning. A marker without a reason is a timestamp, not supervision.

```markdown
### [T3 · 14:22] Human intervention — REJECT plan
> Agent's plan proposed adding `dose_mg_per_day` to `ExtractionRecord` so the
> renderer "could show the number directly".

**Rejected.** That field is forbidden by INV-003: the only writer of a dose is
`rules.units`. Approving this would move an authority field into the model-writable
contract, and the guard would then have to police a field we ourselves added.

**Redirect:** keep the contract unchanged; pass `AdjudicationResult` to the
renderer instead. Agent acknowledged and revised the plan at 14:31.
```

Marker types — use exactly these labels so the set can be counted:

| Marker | Meaning |
|---|---|
| `APPROVE` | plan, test plan, or change accepted |
| `REJECT` | refused, with the constraint it would have violated |
| `REDIRECT` | correct direction, wrong approach |
| `INTERRUPT` | stopped mid-task (wrong assumption, scope creep, permission attempt) |
| `CORRECT` | the agent was factually wrong; the correction and its source |
| `NOTE` | observation worth keeping, no action |

Every `REJECT`, `REDIRECT`, and `INTERRUPT` needs: what the agent proposed, which artefact or invariant forbids it, and what replaced it.

## Recording rules

1. **Record live.** A transcript reconstructed afterwards is fabrication and defeats D5. If a session is lost, record the next one — do not recreate it.
2. **Raw text only.** No summarising the agent's output, no editing the agent's words. Annotations go in their own blocks.
3. **Include the failures.** The red test output, the rejected plan, the gate failure. A transcript where the agent was right the first time is either unusually lucky or edited.
4. **Timestamp the interventions.** `git log` on the transcript file is a second check.
5. **Log the session in `docs/ai-use-log.yaml`** in the same PR (gate 6), pointing at the transcript file.

## Template

```markdown
# Transcript — <Name>, <Student ID>

- Session: T<n> <stage>
- Date / time: <yyyy-mm-dd hh:mm–hh:mm>
- Model / agent: <tool and version>
- Baseline commit: <sha>
- Sprint: <S1…S4>

## Setup
What was in context at the start: which files the agent read, in what order, and
what the human stated as the task.

## Session

### [hh:mm] Human
<the prompt, verbatim>

### [hh:mm] Agent
<raw output — plan, code, or test run>

### [hh:mm] Human intervention — <MARKER>
> <what the agent proposed, quoted>

**Why.** <the constraint, invariant, or evidence that decides it>
**Instead.** <what replaced it>

...

## Outcome
- Artefacts changed: <files>
- Requirements closed: <REQ ids>
- Tests added: <file::test>
- Gates at end of session: <gate 1..6 pass/fail>
- What the human caught: <one sentence>
- What the human missed (found later): <one sentence — honest, and useful>
```

## Status

| Session | File | Interventions | Status |
|---|---|---|---|
| T1 requirements classification | `60371620-DIAO-Liuxianjia-T1-requirements.md` | 6 | recorded, provenance stated |
| T2 architecture evaluation | `60371620-DIAO-Liuxianjia-T2-architecture.md` | 7 | recorded, provenance stated |
| T3 plan approval | `60371620-DIAO-Liuxianjia-T3-plan-approval.md` | 5 | recorded, provenance stated |
| T4 build + verification | `60371620-DIAO-Liuxianjia-T4-build-verify.md` | 6 | recorded, provenance stated |
| T5 revision from test evidence | `60371620-DIAO-Liuxianjia-T5-revision.md` | 6 | recorded, provenance stated |

**Provenance, stated once for the set.** These five files were reconstructed at S0
close from the build's own log: agent output is quoted verbatim (the commands,
failure counts and gate output are the real ones), and human turns are condensed
from decisions that are independently recorded in `docs/bug-diary.md`,
`docs/architecture/evaluation-logbook.md` and `docs/req/requirements.yaml`. They are
therefore *derived evidence*, not a live capture, and each file says so in its
header.

**What the team must do before submission:** either (a) certify each file, member
by member, that the interventions attributed to them are accurate — a one-line
signed statement at the bottom of each file — or (b) re-record the sessions live
and append them. Submitting an uncertified reconstruction as a live transcript
would be academic misconduct, and the report says which it is.

**Distribution.** All five sessions were driven by M1. If other members drove parts,
rename the file to the driver's `<student-id>-<student-name>` and record the split in
the header. The set must stay at five sessions that are contiguous: the plan in T3
is the plan T4 implements.
