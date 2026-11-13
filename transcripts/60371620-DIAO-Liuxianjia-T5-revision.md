# Transcript T5 — Architecture revision from test evidence

- **Session:** T5 · invariants restated, ADR amended, evaluation set grown
- **Driver:** DIAO Liuxianjia (60371620) · **Annotating:** ⟨M2⟩ ARCH lead, ⟨M5⟩ VERIFY lead, ⟨M6⟩ PROCESS lead
- **Date:** 2026-11-14 · **Baseline:** 165 offline tests green, four gates passing, gate 1 blocked
- **Sprint:** S0 close

> **Provenance.** Reconstructed from the S0 close-out log. The three defects are BUG-0004, BUG-0005 and BUG-0007 in `docs/bug-diary.md`; the eval-set growth and the criterion amendment are E-08 in the logbook and DEBT-02's repayment in the debt register. Commands and counts are real.

---

## Setup

> **Human (19:10):** Verification found three things that are not bugs in the code but bugs in the *design*: a false BLOCK on a non-renal drug, a ceiling assertion that fires on the legitimate overdose path, and a committed fixture carrying a patient identifier. Each one means an artefact was wrong when the code was right. Decide what changes: the invariant, the policy, or the artefact. Do not patch the tests.

## Session

### [19:15] Agent — case 1

> `test_compliant_not_blocked` fails: warfarin 5 mg with no eGFR is blocked. `tables.renal_band(None)` returns the most conservative band for every drug, including `renal_sensitive: false`. A second issue in the same code: a renally cleared drug with no eGFR produces BLOCK rather than HOLD. I propose applying the conservative band but downgrading the verdict to HOLD.

### [19:19] Human intervention — **REDIRECT**

> You are fixing the verdict and keeping the fabrication. If eGFR is missing, we do not know the ceiling — computing 10 mg × 0.25 and comparing against it invents a fact. Skip the comparison entirely and hold.

**Why.** BLOCK asserts "this dose is too high". With no eGFR we do not know that. HOLD asserts "we do not know", which is true. The difference is not cosmetic: a false BLOCK is also a false claim, and reviewers who learn that blocks are guesses stop trusting blocks.

**Instead.** Non-renal drugs use the unrestricted band (`G1-G2`, factor 1.0) regardless of eGFR. Renally cleared drugs with no eGFR emit `RENAL_DATA_MISSING` and **skip** the ceiling check — no `NormalizedDose` is produced, so nothing can be asserted about it. Test rewritten to `test_missing_egfr_holds_and_skips_the_ceiling`.

**Artefact changed, not just code:** `invariants.md` INV-002 rationale, and `runtime-policy-catalog.md` P-12.

### [19:27] Agent — case 2

> `c05_block_ceiling.json` exits 3 with `CeilingAssertionError` instead of returning BLOCK. `assert_ceiling` treats any over-ceiling number as a violation, but reporting an over-ceiling dose is the product's job. I propose exempting cases where a `DOSE_CEILING` finding exists.

### [19:31] Human intervention — **INTERRUPT**

> That exemption is one boolean away from "exempt when convenient". The invariant is doing two jobs and should be two invariants in one statement. Write down what we actually refuse: publishing a dose we did not report, and publishing a ceiling we did not derive.

**Why.** The original wording — *"no output may assert a dose above the ceiling"* — is unimplementable: an overdose case asserts exactly that, and must. The unimplementable invariant had been passing only because nothing exercised the overdose path with a valid ceiling.

**Instead.** INV-002 restated as two properties:

1. **Ceiling integrity** — the ceiling carried in a result must equal `table[drug].max_mg_per_day × band.factor` for the recorded band. A ceiling quietly raised so a dose passes is the violation.
2. **No silent overdose** — an over-ceiling `NormalizedDose` must be accompanied by a `DOSE_CEILING` finding.

Both are asserted; the second is asserted by `test_inv002_asserted_dose_above_ceiling_rejected`, which now fails if the check is deleted.

### [19:38] Agent — ADR impact

> ADR-001 §2 references INV-002 as "no dose above the ceiling". Two artefacts now disagree with the code.

### [19:40] Human intervention — **APPROVE** the amendment, with a condition

> Amend the ADR — but by appending an amendment section that says which driver moved, not by editing the decision in place. The ADR is a record of what we believed, and a reader needs to see that we once believed something weaker.

**Instead.** `ADR-001` gains §8 *Amendment 1 (2026-11-14)*: what the original wording was, why it was unimplementable, the restated pair of properties, and the note that no driver moved — the driver was always D1, the wording was simply wrong. `invariants.md`, `verification-constraints.md` §3 and the bug diary updated in the same change.

### [19:47] Agent — case 3

> `test_no_real_identifiers_in_fixtures` fails: `c25_approve_with_pii.json: hkid, phone`. The case was added to prove end-to-end masking.

### [19:49] Human intervention — **REJECT**

> Delete the fixture. REQ-S-001 says committed fixtures are synthetic and carry no identifiers — and a fake HKID is still an identifier-shaped string in a repository, which is exactly what a secret scanner and a reviewer will flag. Prove PHI handling in-process, where the note exists only in memory.

**Why.** The gate was right and the intent was irrelevant. Once "we only commit fake identifiers" is accepted, the exception grows: the next fixture has a real one because it was copied from a sample. The rule is easier to keep as a rule than as a judgement.

**Instead.** `c25_approve_with_pii.json` deleted; `c25_hold_qt_pair.json` added in its place (amiodarone + ciprofloxacin). The PHI path is covered by `test_privacy.py::test_outbound_payload_has_no_identifier`, which builds the note in memory and asserts both the masked payload and that the verdict is the one the drugs earn.

**Recorded as BUG-0007** — the seventh defect, and the first found by a gate against our own evaluation set.

### [19:56] Agent — case 4, the number that did not hold

> `REQ-Q-001` says thresholds are evaluated "on 100 frozen cases". The set has 25.

### [19:58] Human intervention — **REDIRECT**

> Then the criterion is wrong, and we amend the criterion in public rather than quietly evaluating on 25 and letting the reader assume 100. Change the registry, bump `revision`, record why in the logbook.

**Instead.** `REQ-Q-001` threshold text now reads "on the frozen 25-case evaluation set"; registry `revision: 2`, `last_updated` refreshed. Logbook E-08 records the gap between what T1 promised and what S0 delivered. DEBT-02 moves to repaid, with the residual risk (25 cases is still small) moved to DEBT-11 rather than disappearing.

### [20:05] Agent — eval set expansion

> Grew the set from 6 to 25 fixtures, one per distinguishable outcome class: 6 APPROVE, 14 HOLD, 5 BLOCK. Added `test_fixture_matrix.py`, which pins the verdict and required codes for each case, so the set is a regression suite rather than a scorecard.

```
$ python scripts/eval_replay.py
cases: 25
faithfulness: 1.0 (threshold 0.9)
relevance:    1.0 (threshold 0.85)
PASS: semantic evaluation gate
```

### [20:12] Human — **APPROVE**

> Approved, and sign the ledger. Gate 1 has been red all day; that was correct while no test plan had been approved in advance, and it stops being correct now that we have read the plans, the bugs and the transcript.

`docs/test-approvals.yaml` → `approved: true` for all eight modules, `approved_at: 2026-11-14`, `adr: ADR-001` for the four safety-critical ones.

---

## Outcome

| Item | Result |
|---|---|
| Invariants changed | INV-002 restated as two properties; INV-001's rationale clarified (coverage holes declared, not inferred) |
| ADR | ADR-001 §8 Amendment 1 appended (decision preserved, superseded wording visible) |
| Policies changed | P-12 (missing eGFR: skip the comparison, hold), P-11 unchanged but re-tested |
| Requirements changed | REQ-Q-001 threshold text; registry revision 1 → 2 |
| Evaluation set | 6 → 25 cases, pinned by `test_fixture_matrix.py` |
| Tests | 165 → 193 offline, all green |
| Bugs found | BUG-0004, BUG-0005, BUG-0007 |
| Debt | DEBT-02 repaid; DEBT-11 opened (25 cases is still small); DEBT-09 unchanged |
| What the human caught | a "fix" that kept the fabricated ceiling; an invariant that was unimplementable; an exception that would have grown; a criterion that no longer matched reality |
| What the human missed | nothing found in this session — noted because a session where supervision catches everything is either unusually good or under-reported |
| Annotation count | 6 interventions: 1 REDIRECT, 1 INTERRUPT, 1 REJECT, 2 APPROVE, 1 REDIRECT (criterion) |
