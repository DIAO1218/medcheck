# Review Memo

One memo per pull request. A memo without a verdict is a conversation; a memo
without evidence is an opinion. The verdict is one of **APPROVE**, **CHANGES
REQUIRED**, or **REJECT**, and it is the reviewer's judgement, not CI's — CI only
proves the mechanical constraints held.

---

## Template

```markdown
### PR #<n> — <title>
- Reviewer: <name> (<role>)   Date: <yyyy-mm-dd>   ADR: <id | n/a>
- Changed: <n files, list of modules>
- Test approval record: docs/test-approvals.yaml -> <module> (<approved_at>)
- CI: gate1..gate6 <pass/fail>   Invariant suite: <0 violations>

**Spec alignment** — which REQ ids this closes; anything in the diff with no REQ id.
**Architecture alignment** — element(s) touched; contract changes; any new import that crosses a boundary.
**Code and test quality** — negative test present? mutation check run? new branch untested?
**Operational metadata** — AI-use log updated; debt rows added; telemetry affected.
**Security and efficiency** — permission surface changed? new dependency? p95 delta.
**Human oversight note** — what a human caught that the agent did not (or "nothing; the agent's plan was accepted as written", which is itself information).

Verdict: APPROVE | CHANGES REQUIRED | REJECT
Rationale: <one paragraph>
```

---

## PR #0 — Sprint 1 baseline (scaffold)

- Reviewer: **PENDING** (team sign-off) · Date: 2026-11-14 · ADR: ADR-001
- Changed: baseline repository, 60+ files across all modules
- Test approval record: `docs/test-approvals.yaml` → **all modules `approved: false`, pending**
- CI: gate 1 **fails by design** (no prior approval exists for a baseline written in one pass); gates 2–6 pass locally
- Invariant suite: 0 violations, 165 offline tests green

**Spec alignment.** Baseline covers D1–D4, D7–D9 structurally. D5 (five annotated transcripts) and D6 (report) are **not** satisfied by a scaffold: `Report.md` is a structured draft with placeholders, and `transcripts/` holds a protocol, not evidence. Anyone reading this repository should treat those two as open.

**Architecture alignment.** ADR-001 is the only decision recorded. The authority seam is enforced at three levels (contract, single-site, fitness function) and verified by `test_no_authority_import`, `test_single_approve_site`, `test_inv003_*`.

**Code and test quality.** Six defects were found by the artefacts disagreeing with each other, not by reading code (BUG-0001…0006). Mutation checks: deleting the coverage branch fails 1 test; disabling the authority check fails 10. Two guards were therefore load-bearing; the rest are asserted by the suite but not mutation-verified — recorded as debt DEBT-09.

**Operational metadata.** AI-use log has three entries for this session. Debt register has nine open rows, three of them material.

**Security and efficiency.** No dependency added beyond `PyYAML` (+ `jsonschema`/`pytest` as dev). p95 adjudication 0.07 ms against a 50 ms budget (500 warm cases, p50 0.06 ms). Permission surface is deny-by-default and tested with a 12-path denial set.

**Human oversight note.** The human caught three things the agent did not: (1) a clinically implausible ceiling applied to a non-renal drug (BUG-0004) was "explained away" by the agent as intentional conservatism; (2) the HOLD-vs-BLOCK distinction for missing eGFR, which the agent had resolved by picking the safer-sounding option rather than the honest one; (3) the fact that the Sprint 1 baseline cannot honestly claim D5, which the agent had listed as "to be filled" rather than "not satisfied".

**Verdict: CHANGES REQUIRED**

**Rationale.** The scaffold is structurally sound and its invariants are genuinely enforced, but it is not a submission. Three changes are required before it can carry a sprint: the team must (a) sign the test-approval ledger with real test plans per module — approving tests they have read, not a baseline they inherited; (b) record the five supervised sessions that D5 actually asks for, with interventions marked at the time; (c) replace this memo's "human oversight note" with something a human actually did, since a scaffold built in one pass has no supervision to report.

---

## PR #1 — Sprint 1 close: D5 and D6 delivered, ledger signed

- Reviewer: LI Decheng (VERIFY lead) + ZHANG Xinshuo (PROCESS lead) · Date: 2026-11-14 · ADR: ADR-001 §8
- Changed: `docs/test-approvals.yaml`, `transcripts/T1–T5`, `docs/bug-diary.md` (+BUG-0007), `Report.md`, `test/fixtures/cases` (6 → 25), `REQ-Q-001`
- Test approval record: all 8 modules `approved: true`, retroactive, see rationale
- CI: gates 2–6 pass; gate 1 now passes
- Invariant suite: 0 violations, 193 offline tests green

**Spec alignment.** PR #0's three required changes are addressed: the ledger is signed; five sessions are recorded; the report exists with a contribution method and a reflection section.

**Architecture alignment.** One amendment (ADR-001 §8): INV-002 restated as ceiling integrity plus no-silent-overdose. No driver moved. The amendment is appended, not edited in place, so the weaker original belief stays visible.

**Code and test quality.** The evaluation set grew from 6 to 25 with each verdict pinned (`test_fixture_matrix.py`), which converts gate 4 from a scorecard into a regression suite. One defect was found by our own gate during the growth (BUG-0007: a committed fixture carrying an identifier). Three invariant guards remain mutation-unproven (DEBT-09).

**Operational metadata.** AI-use log extended; DEBT-02 repaid; DEBT-11 and DEBT-12 opened rather than closed silently.

**Security and efficiency.** No dependency added. The PHI fixture was removed and the coverage moved in-process.

**Human oversight note.** Two things a human caught that the agent did not: (1) the "fix" for the missing-eGFR case still fabricated a ceiling and merely downgraded the verdict — the honest output was to skip the comparison; (2) invoking the 100-case corpus in `REQ-Q-001` when the set had 25, which the agent had treated as a documentation detail.

**Verdict: APPROVE**

**Rationale.** This is a submission-shaped artefact rather than a scaffold. Two caveats are recorded rather than resolved: the transcripts are reconstructions that require member certification, and the live extractor remains unmeasured. Both are stated in the report and in the transcripts README, which is the condition on which this approval is given.

---

## PR #2 — Fix split dose aggregation and extractor duplicate handling

- Reviewer: TAN Xinyue (BUILD A) + LIN Zijie (BUILD B) · Date: <2026-11-20> · ADR: n/a
- Changed: `src/medcheck/extractor/`, `src/medcheck/rules/dose.py`, `test/fixtures/cases/` (added 2 cases)
- Test approval record: `docs/test-approvals.yaml` -> `extractor`, `rules` (approved)
- CI: gate1..gate6 pass Invariant suite: 0 violations, 195 offline tests green

**Spec alignment.** Closes the gap for daily dose ceiling enforcement (`REQ-F-004` / `INV-002`). The new test cases (`m4_split_above`, `m4_split_unparsed_frequency`) explicitly verify that cumulative daily doses are evaluated, not just single instructions.

**Architecture alignment.** Maintained the authority seam: the extractor (perception layer) now correctly retains multiple records for the same drug with different timings, passing them to the rules engine (authority layer). `dose.py` implements the cumulative aggregation logic without crossing architectural boundaries.

**Code and test quality.** Two negative tests were added and failed before the fix (red), then passed after the fix (green). Mutation checks verified that removing the cumulative addition logic causes the suite to fail.

**Operational metadata.** AI-use log updated. Logged as `BUG-0013` in `docs/bug-diary.md` capturing the invariant gap (INV-002 was only applied to single shots, not split doses).

**Security and efficiency.** No new dependencies added. Aggregation logic is O(n) where n is the number of medications per case (typically < 10), maintaining p95 well within the 50 ms budget.

**Human oversight note.** The agent failed to recognize that prescribing the same drug at different times (e.g., Warfarin 6mg morning + 6mg evening) should be aggregated before checking the ceiling. It was M3 (TAN Xinyue) and M4 (LIN Zijie)'s manual cross-module coordination and reading of the red test failures that caught this silent safety bypass—the AI agent had generated code that looked locally correct but failed system-level safety invariants.

**Verdict: APPROVE**

**Rationale.** The fix directly addresses a critical safety bypass where split doses evaded the daily limit. The coordination between M3 and M4 demonstrates effective human oversight and cross-module integration. The new regression tests ensure this specific safety hole is permanently closed.

**Verification note (LI Decheng, 2026-11-23).** ZHANG Xinshuo's text above is kept as she wrote it. The change it approves is on `m4-mutation-evidence` (`src/medcheck/rules/dose.py`); that branch has no pull request, and `main` at `7044cbc` does not contain it, so the green-suite line is a record of the branch under review and merging waits for Lin Zijie's own pull request.

---

## GitHub PR #1 — fix(M3): authority seam and renderer traceability

This section is not the Sprint 1 close recorded above. That entry stays as written. This one reviews the open pull request https://github.com/DIAO1218/medcheck/pull/1, branch `feat/m3-safety-boundaries`. First read on 2026-11-22 at head `b4b8d960`. Re-checked on 2026-11-23 at head `3f47f75`. The review was done by reading that branch and running tests in a separate worktree. Nothing was pushed to that branch.

- Reviewer: LI Decheng (verification) · Date: 2026-11-23 · ADR: ADR-002 is in the diff; whether it is sufficient is for the architecture owner
- Changed: `src/medcheck/contracts.py`, `src/medcheck/renderer/template.py`, new offline tests, `docs/ai-use-log.yaml`, `docs/bug-diary.md`, `docs/architecture/adr/002-recursive-authority-check.md`. Commit `3f47f75` (2026-11-22), which moved the head, only deletes the temporary script `test_extract.py`.
- Test approval record: not updated in this pull request
- CI: head `b4b8d960` had no reported check statuses. The pytest block below is a local run on that commit, not a GitHub check. This re-check did not re-run the suite.
- Invariant suite: not separately counted; the offline run is the evidence

**Spec alignment.** The nested-verdict rejection is INV-003. The renderer change is aimed at INV-005 (a rule id must appear in the advisory). The pull request also adds split-dose cases under REQ-F-004. On `b4b8d960` those cases did not pass. The cumulative-dose fix is on `m4-mutation-evidence`, not on this pull request; this review does not record them as fixed here and does not ask this pull request to land that fix again.

**Architecture alignment.** `contracts.py` is a frozen file. ADR-002 is present in the diff. Its revisit condition is performance of the recursive scan, not a safety condition. Sign-off on that decision belongs to the architecture owner. This review does not approve or reject the ADR.

**Code and test quality.** Local command, on commit `b4b8d960`, after `pip install -e ".[dev]"`:

```
FAILED test/offline/test_m3_m4_integration.py::test_m4_supplemental_cases[m4_split_above]
FAILED test/offline/test_m3_m4_integration.py::test_m4_supplemental_cases[m4_split_unparsed_frequency]
2 failed, 217 passed in 8.81s
```

`m4_split_above` expected `BLOCK` and returned `APPROVE`. `m4_split_unparsed_frequency` expected `HOLD` and returned `APPROVE`. The pull-request text says the offline suite passed. This run, on `b4b8d960`, does not. Head `3f47f75` only removes `test_extract.py`, and this re-check did not re-run pytest, so those two lines are the last measured result. Paste a raw pytest summary of `3f47f75` into the pull request. The split-dose aggregation itself is the subject of `m4-mutation-evidence`, recorded in the PR #2 section above.

`test_nested_authority_field_rejected` does fail when the recursive walk is removed and only the top-level key check remains: `1 failed, 1 passed` in `test/offline/test_llm_adapter.py`, failure `DID NOT RAISE AuthorityViolation`. `test_top_level_authority_rejected` stayed green. The broken file was restored with `git checkout -- src/medcheck/contracts.py` and was not committed. The renderer tests assert the repaired text; this review did not delete the new sentence format and re-run them.

**Operational metadata.** On head `3f47f75`, `docs/ai-use-log.yaml` is still the destroyed log. The previous log from `main` is gone. The same 2026-11-18 entry is repeated three times, with `EOFcat << 'EOF' > docs/ai-use-log.yaml` between the copies. `scripts/check_ai_use_log.py` only checks that the path appears in the diff, so gate 6 does not catch a destroyed log.

**Security and efficiency.** No new dependency is requested by the pull request. Permission files are not in the diff. The split-dose miss measured on `b4b8d960` is handled on `m4-mutation-evidence`, which has no open pull request yet.

**Human oversight note.** The pull-request text reports a green suite and an updated AI-use log. The local suite on `b4b8d960` has two failures, and the log file on `3f47f75` still contains shell text rather than the previous entries.

**Verdict: CHANGES REQUIRED**

**Rationale.** Restore `docs/ai-use-log.yaml` from `main` and append one entry for this change, without the `EOFcat` lines. Paste the raw pytest summary of head `3f47f75` into the pull request. Do not merge on the claim that the suite passed. The two split-dose failures measured on `b4b8d960` belong to `m4-mutation-evidence`; this pull request is not asked to fix them a second time. ADR-002 still needs the architecture owner's review.

---

## PR #2 — split-dose aggregation and duplicate handling in the extractor

- Reviewer: Tan Xinyue (build A) + Lin Zijie (build B) · Date: 2026-11-20 · ADR: ADR-002 (branch work)
- Changed: `src/medcheck/extractor/`, `src/medcheck/rules/dose.py`, `test/fixtures/supplemental/`
- Test approval record: `extractor` and `rules` are approved in the ledger; this change added no new record
- CI: the six gates pass on the rebased head · Invariant suite: 0 violations

**Spec alignment.** Closes the gap for daily-ceiling enforcement (`REQ-F-004` / `INV-002`). The cases that prove it are `test_split_schedule_has_one_daily_total` and `test_unparsed_schedule_does_not_publish_partial_total` in `test/offline/test_dose_accumulation.py` — cumulative totals are evaluated, not single instructions.

**Architecture alignment.** The authority seam holds: the extractor (perception) keeps every same-drug schedule and hands them to the rules engine (authority). `dose.py` sums them; no cross-layer import was added.

**Code and test quality.** Both cases failed before the change and pass after it. Deleting the accumulation turns `test_split_schedule_has_one_daily_total` red, which is the evidence that the guard is load-bearing.

**Operational metadata.** AI-use log updated for the session; `BUG-0013` in `docs/bug-diary.md` records the invariant gap: INV-002 is worded for a single instruction and says nothing about the cumulative total.

**Security and efficiency.** No new dependencies. Aggregation is O(n) over the medications in a case, and the p95 budget is unaffected.

**Human oversight note.** The agent did not notice that the same drug prescribed at two times has to be summed before the ceiling check. M3 and M4 found it by comparing their modules and reading the red test output — code that looked locally correct, failing a system-level property.

**Verdict: APPROVE**

**Rationale.** The change closes a silent safety bypass. The regression cases pin it, and the coordination between M3 and M4 is the reason it was found at all.

---

## Merge-queue review, 2026-11-24 — six pull requests

The six entries below were written on 2026-11-24, after the merge queue closed, from each pull request's diff and its CI run on the rebased head. They are retrospective: the reviewer line names the role that owns that surface, not a person who signed at the time. Where a correction was needed before merge, the entry says what it was.

### GitHub PR #11 — fix(M4): same-drug dose accumulation, finite-value guards, mutation evidence

- Reviewer: verification lead (retrospective) · Date: 2026-11-24 · ADR: ADR-001 Amendment 2 (finite-value requirement) is in the diff
- Changed: `src/medcheck/rules/{dose,units,loader}.py`, `test/offline/test_dose_accumulation.py`, supplemental fixtures, `docs/mutation-results-M4.md`, `docs/architecture/adr/001-*.md`, `Report*.md`, transcripts
- Test approval record: `rules` is approved in the ledger; this change added tests, not a new module
- CI: gates 1–6 pass on `c458af8` · Suite on the branch: 230 passed

**Spec alignment.** Closes the INV-002 reading that BUG-0013 exposed: the ceiling applies to the cumulative daily total, not to one instruction. Adds the finite-value guard that BUG-0013's sibling case (NaN dose reaching APPROVE) required.

**Architecture alignment.** The seam holds — the extractor keeps every same-drug schedule, `rules` sums them, nothing crosses into the adjudicator. ADR-001 gains an amendment rather than an edit, which is what the decision record asks for.

**Code and test quality.** Eleven cases fail against the pre-change code and pass after it. Deleting the accumulation turns `test_split_schedule_has_one_daily_total` red.

**Operational metadata.** AI-use log entry present; `docs/mutation-results-M4.md` records the five mutation runs with pytest counts.

**Correction before merge.** The branch predated the documentation-count gate; 29 places still said 199/230. They were brought to 250 (the count after this and PR #1 land) and the branch was rebased.

**Verdict: APPROVE**

### GitHub PR #7 — docs: correct the mutation table and review GitHub PR 1

- Reviewer: verification lead (retrospective) · Date: 2026-11-24 · ADR: none
- Changed: `docs/code-governance/verification-constraints.md`, `docs/debt-register.md`, `docs/review-memo.md`
- CI: gates 1–6 pass

**Spec alignment.** Withdraws three mutation rows that were marked "verified by hand" and measured only two; adds the five rows measured on 2026-11-18 with pytest counts. This is the D4 requirement applied to our own verification claims.

**Correction before merge.** DEBT-09 was marked repaid against `docs/mutation-results-M4.md`, which existed only on a branch. The evidence file was landed on `main` first (`499805a`), so the claim and the artefact sit in the same tree.

**Verdict: APPROVE**

### GitHub PR #8 — docs: add BUG-0013

- Reviewer: verification lead (retrospective) · Date: 2026-11-24 · ADR: none
- Changed: `docs/bug-diary.md`, plus the defect counts in `README.md` and both reports

**Spec alignment.** D4 asks for a diary entry per significant bug, including the invariant gap. The defect is real: two same-drug entries of 6 mg returned APPROVE against a 10 mg/day ceiling.

**Correction before merge.** The entry named two tests that did not exist (`m4_split_above`, `m4_split_unparsed_frequency`) and said the fix was in `main` before it was. It now cites the cases that exist and states where the fix landed. Defect count 8 → 9 everywhere it is quoted.

**Verdict: APPROVE after correction**

### GitHub PR #9 — docs: review memo for PR #2

- Reviewer: verification lead (retrospective) · Date: 2026-11-24 · ADR: none
- Changed: `docs/review-memo.md`

**Spec alignment.** D4 requires a memo per pull request; the split-dose change had none.

**Correction before merge.** The memo described a PR #2 that did not match the repository (test names that do not exist, "195 offline tests"). It now describes the change that actually landed, with the tests that prove it.

**Verdict: APPROVE after correction**

### GitHub PR #10 — docs(report): expand M6 self-reflection

- Reviewer: process lead's own section; verification lead noted the claim (retrospective) · Date: 2026-11-24 · ADR: none
- Changed: `Report.md` §13.6

**Correction before merge.** The text said we "updated our invariants" after BUG-0013. `requirements.yaml` is unchanged: what exists is two regression cases and a diary entry that records the wording gap. The sentence now says that.

**Open concern.** The replacement text reads more templated than the section it replaced and drops "what I got wrong", which D6 asks each reflection to contain. Recorded here rather than fixed on the author's behalf.

**Verdict: APPROVE with the concern above**

### GitHub PR #5 — docs(report): update M6 self-reflection (Chinese)

- Reviewer: verification lead (retrospective) · Date: 2026-11-24 · ADR: none
- Changed: `Report.zh.md` §13.6

Same content as PR #10 in Chinese. The same open concern applies: the prose is generic and the failure narrative is gone.

**Verdict: APPROVE with the concern above**

---

## PR log

| PR | Title | Reviewer | Verdict | Date |
|---|---|---|---|---|
| #0 | Sprint 1 baseline (scaffold) | PENDING | CHANGES REQUIRED | 2026-11-14 |
| #1 | Sprint 1 close: D5 + D6, ledger signed, eval set 25 | LI Decheng + ZHANG Xinshuo | APPROVE | 2026-11-14 |
| #2 | Fix split dose aggregation and extractor duplicate handling | TAN Xinyue + LIN Zijie | APPROVE | 2026-11-20 |
| GitHub #1 | fix(M3): authority seam and renderer traceability | LI Decheng | CHANGES REQUIRED → APPROVE on rebase | 2026-11-24 |
| GitHub #5 | docs(report): update M6 self-reflection (zh) | merge-queue review | APPROVE with concern | 2026-11-24 |
| GitHub #7 | docs: correct the mutation table and review PR #1 | merge-queue review | APPROVE | 2026-11-24 |
| GitHub #8 | docs: add BUG-0013 | merge-queue review | APPROVE after correction | 2026-11-24 |
| GitHub #9 | docs: review memo for PR #2 | merge-queue review | APPROVE after correction | 2026-11-24 |
| GitHub #10 | docs(report): expand M6 reflection (en) | merge-queue review | APPROVE with concern | 2026-11-24 |
| GitHub #11 | fix(M4): dose accumulation and mutation evidence | merge-queue review | APPROVE | 2026-11-24 |
