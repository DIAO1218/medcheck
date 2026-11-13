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

## PR #0 — S0 baseline (scaffold)

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

**Human oversight note.** The human caught three things the agent did not: (1) a clinically implausible ceiling applied to a non-renal drug (BUG-0004) was "explained away" by the agent as intentional conservatism; (2) the HOLD-vs-BLOCK distinction for missing eGFR, which the agent had resolved by picking the safer-sounding option rather than the honest one; (3) the fact that the S0 baseline cannot honestly claim D5, which the agent had listed as "to be filled" rather than "not satisfied".

**Verdict: CHANGES REQUIRED**

**Rationale.** The scaffold is structurally sound and its invariants are genuinely enforced, but it is not a submission. Three changes are required before it can carry a sprint: the team must (a) sign the test-approval ledger with real test plans per module — approving tests they have read, not a baseline they inherited; (b) record the five supervised sessions that D5 actually asks for, with interventions marked at the time; (c) replace this memo's "human oversight note" with something a human actually did, since a scaffold built in one pass has no supervision to report.

---

## PR #1 — S0 close: D5 and D6 delivered, ledger signed

- Reviewer: ⟨M5⟩ VERIFY lead + ⟨M6⟩ PROCESS lead · Date: 2026-11-14 · ADR: ADR-001 §8
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

## PR log

| PR | Title | Reviewer | Verdict | Date |
|---|---|---|---|---|
| #0 | S0 baseline (scaffold) | PENDING | CHANGES REQUIRED | 2026-11-14 |
| #1 | S0 close: D5 + D6, ledger signed, eval set 25 | ⟨M5⟩ + ⟨M6⟩ | APPROVE | 2026-11-14 |
