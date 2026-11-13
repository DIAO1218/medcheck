# Submission checklist

Everything in this repository is either **done and verified** or **listed here as yours to do**. Nothing in between: a blank cell is honest, a plausible invention is not.

Run every command in §1 before you zip. It takes about 15 seconds and it is the difference between a submission and a claim.

---

## 1. Verify before you submit

```bash
pip install -e ".[dev]"

python scripts/validate_requirements.py          # gate 3
python -m pytest test/offline -q                 # gates 2 + 5  → expect 193 passed
python scripts/eval_replay.py                    # gate 4      → expect 25 cases, 1.0 / 1.0
python scripts/check_permissions_sync.py         # gate 2
python scripts/build_ddi_fixtures.py --check     # fixtures not stale
python scripts/check_test_approval.py --changed src/medcheck/rules/dose.py   # gates 1 + 6
python scripts/check_ai_use_log.py --changed src/medcheck/rules/dose.py docs/ai-use-log.yaml
```

All seven must print `PASS`. If one fails, the failure is real — do not edit the check.

## 2. Fill in the six identities (only you can do this)

| Where | What |
|---|---|
| `Report.md` §1 mapping table | real name + student number for ⟨M1⟩–⟨M6⟩ |
| `Report.md` §1 hours table | per-sprint productive hours, then compute weights with the formula |
| `Report.md` §13 | each member rewrites their own reflection in their own voice, then signs it |
| `transcripts/*.md` headers | replace `⟨M1⟩`–`⟨M6⟩` in the "Annotating" lines with real names |
| `docs/test-approvals.yaml` | `approved_by: "S0 close review (⟨M1⟩–⟨M6⟩)"` → real names |
| `README.md` bottom | the real GitHub URL |

**Do not invent hours.** The weight formula divides by the mean; invented inputs produce a distribution that looks authoritative and is fabricated. An empty cell that you fill honestly is worth more than a plausible one.

## 3. Certify the transcripts, or re-record them

The five files in `transcripts/` are **reconstructions** from the build log, with agent output quoted verbatim and human turns condensed from recorded decisions. Each file says so in its header.

D5 asks for recorded sessions with marked interventions. You have two honest options:

- **(a) Certify.** Read each file, confirm the interventions attributed to you are accurate, and append a signed line: `Certified: <name>, <student id>, <date>`. Then state in `Report.md` §6.3 that the set is certified reconstruction.
- **(b) Re-record.** Run the five sessions live (the stages are defined in `transcripts/README.md`) and append them as new files. This is stronger evidence and costs most of a day.

Submitting (a) as though it were live capture is academic misconduct. The report currently says which it is; keep it that way.

## 4. Optional but high-value, in this order

| # | Task | Why it matters | Effort |
|---|---|---|---|
| 1 | Measure the live extractor on 20 real-ish notes, fill `prompts/prompt_v1.0.yaml: live_accuracy` | the only claim in the report that is currently `null` (DEBT-06) | half a day |
| 2 | Mutation-check INV-002 / 004 / 005, record in `verification-constraints.md` §3 | turns "5 invariants" into "5 proven" (DEBT-09) | 1 hour |
| 3 | 20% human audit of the 25-case set, record disagreement rate | makes the semantic score meaningful rather than a proxy (DEBT-01) | 2 hours |
| 4 | Add 10 generated multi-drug cases | the APPROVE family is under-covered (DEBT-11) | 2 hours |

If you do only one, do #1: a measured null is the difference between "we built it" and "we know it works".

## 5. Package

```bash
cd "GROUP PROJECT"
zip -r CS5351-MedCheck.zip MedCheck -x "MedCheck/.pytest_cache/*" -x "*/__pycache__/*" -x "MedCheck/data/audit/*"
```

The required structure is preserved inside the zip (`docs/req/`, `docs/architecture/`, `docs/code-governance/`, `src/`, `test/offline`, `test/live`, `transcripts/`, `.opencode/`, `.agent/`, `.github/workflows/`).

## 6. Pre-submission questions the marker will ask

Answer these out loud before you submit; if any answer is "uh", fix the artefact rather than rehearsing.

1. **Show me an invariant that would fail if you deleted the guard.** → INV-001 or INV-003, both mutation-checked.
2. **What does the model decide?** → Nothing. It extracts fields and paraphrases findings; verdict, severity and dose come from deterministic code.
3. **What happens when a drug is not in your table?** → `HOLD` + `COVERAGE_GAP`, never `APPROVE`. Including for pairs you declared unassessed.
4. **Why is a missing eGFR a HOLD and not a BLOCK?** → Because BLOCK asserts the dose is too high, and we do not know that. HOLD asserts we do not know.
5. **Which of your tests would have passed with the bug present?** → The one that is now `test_inv001_unknown_drug_is_not_approved`; it was written before the fix and failed.
6. **What did a human catch that the agent did not?** → §11, three concrete cases. Do not answer this one with a generality.
7. **Where is the honest gap in this project?** → Live extractor unmeasured; three guards mutation-unproven; transcripts are reconstructions; contribution hours are placeholders. Say all four, unprompted.

## 7. Status of the nine deliverables

| # | Deliverable | State |
|---|---|---|
| D1 | requirements + schema | complete, gate-verified (rev 2) |
| D2 | 11 architecture artefacts | complete |
| D3 | coding governance | complete |
| D4 | verification governance | complete (review memo #0 and #1) |
| D5 | five annotated transcripts | recorded — **needs certification or re-recording** |
| D6 | report | complete in content — **needs names, hours, reflections** |
| D7 | repo + six gates | complete, gates self-tested |
| D8 | source + tests | complete (193 offline, 3 live marked) |
| D9 | static prompt | complete |

Two cells still depend on you, and both are marked in the report itself. That is the intended state: the artefacts a team must own are the ones about the team.
