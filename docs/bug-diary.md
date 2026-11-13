# Bug Diary

One entry per significant bug: symptom, reproduction, classification, root cause,
fix, and **which invariant gap it exposed**. The last field is why this file is
not a changelog — a bug that exposes no gap is a bug we got lucky with.

Entries are append-only. A bug found by a gate names the gate; a bug found by
reading code names the reader, because that difference is itself evidence.

---

## BUG-0001 — the schema gate rejected a requirement it should have rejected

| Field | Value |
|---|---|
| **Symptom** | `scripts/validate_requirements.py` failed on the first registry draft: `REQ-P-001` fit criterion `"p95 <= 50 ms."` (14 chars) was shorter than the schema's `minLength: 20`. |
| **Reproduction** | `python scripts/validate_requirements.py` on revision 0 of the registry. |
| **Classification** | Requirements quality — non-falsifiable criterion. |
| **Found by** | CI gate 3 (the gate was written before the registry was finished). |
| **Root cause** | The criterion named a number without naming what was measured, on what corpus, or where the result is reported. The length rule caught it accidentally; the content was the real problem. |
| **Fix** | Rewritten to name the function, the corpus (1000 warm-table cases), the runner, and the owning test. |
| **Invariant gap** | None — but it exposed a **process** gap: "machine-checkable" was being interpreted as "contains a number". Rule adopted: a fit criterion must contain a quantity *and* a measurement site. |

---

## BUG-0002 — the system approved an unassessed drug pair

| Field | Value |
|---|---|
| **Symptom** | A case containing metformin + ciprofloxacin returned `APPROVE`. Both drugs are in the tables; their interaction is *not* enumerated. |
| **Reproduction** | `python -m medcheck.api.cli --case test/fixtures/cases/hold_coverage_hole.json` before the fix returned `APPROVE`. |
| **Classification** | Safety logic — open-world assumption where a closed world was required. |
| **Found by** | Writing the negative test for what became INV-001; the test was expected to pass and did not. |
| **Root cause** | `covers_pair()` treated "pair absent from the table" as "no known interaction". That is true for pairs we *assessed* and false for pairs we never assessed, and the table had no way to distinguish them. Absence of evidence was being read as evidence of absence. |
| **Fix** | Added `coverage_holes` to `ddi.yaml` — pairs declared *unassessed*. `coverage.assess()` emits `COVERAGE_GAP` for unknown drugs **and** for declared holes; the verdict can then never be `APPROVE`. |
| **Invariant gap** | This is the bug that **created INV-001**. The original requirement said "handle unknown drugs safely", which is not testable; it became "verdict ≠ APPROVE, must carry COVERAGE_GAP". |

---

## BUG-0003 — a permission rule was silently disabled by path normalisation

| Field | Value |
|---|---|
| **Symptom** | `check(".env", "plan-agent", "read")` returned **allowed**. |
| **Reproduction** | `test/offline/test_permissions.py::test_default_deny_for_unlisted_path` reported 11 denials instead of 12. |
| **Classification** | Guardrail defect — security control bypassed by a string operation. |
| **Found by** | The 12-path fit criterion in REQ-G-002. Had the criterion said "default deny is configured", it would have passed. |
| **Root cause** | `path.lstrip("./")` strips *characters*, not a prefix: `.env` → `env`, and `.opencode/rules.md` → `opencode/rules.md`. Every deny rule keyed on a leading dot became a no-op. |
| **Fix** | `_normalise()` removes a `./` prefix explicitly and strips only leading slashes, with a comment naming this exact trap. |
| **Invariant gap** | INV-004 was only tested through the *masking* path. A path-based leak of the same data was outside its tests. Added: the denial suite is part of the privacy evidence set. |

---

## BUG-0004 — renal banding applied to drugs that are not renally cleared

| Field | Value |
|---|---|
| **Symptom** | Warfarin 5 mg once daily with no eGFR was flagged `DOSE_CEILING` — a false block. The ceiling had been computed as 10 mg × 0.25. |
| **Reproduction** | `test/offline/test_dose.py::test_compliant_not_blocked`. |
| **Classification** | Safety logic — over-conservative, producing a BLOCK that asserted something false. |
| **Found by** | Offline regression suite, first run. |
| **Root cause** | `tables.renal_band(None)` returns the most conservative band for **all** drugs, including those the table marks `renal_sensitive: false`. Separately, a missing eGFR for a renally cleared drug produced `BLOCK` — claiming the dose was too high when what we actually knew was that we could not evaluate it. |
| **Fix** | Non-renal drugs use the unrestricted band regardless of eGFR. For renally cleared drugs with no eGFR, the ceiling comparison is **skipped** and the case is held (`RENAL_DATA_MISSING`): HOLD asserts "we do not know", which is true; BLOCK would assert a fact we do not have. |
| **Invariant gap** | INV-002 was written as "never above the ceiling" and said nothing about *fabricating a ceiling from a guessed kidney function*. Amended: the ceiling may only be derived from a recorded eGFR or from a drug that does not require one. |

---

## BUG-0005 — the ceiling assertion fired on the legitimate overdose path

| Field | Value |
|---|---|
| **Symptom** | A genuine overdose case raised `CeilingAssertionError` instead of returning `BLOCK`, so no result document and no audit record were produced. |
| **Reproduction** | `python -m medcheck.api.cli --case test/fixtures/cases/block_dose_ceiling.json` → exit 3. |
| **Classification** | Design defect — the invariant was over-broad and collided with normal operation. |
| **Found by** | CLI verdict test expecting `BLOCK`. |
| **Root cause** | `assert_ceiling` treated *any* over-ceiling number as a violation. But reporting an over-ceiling dose is exactly the product's job; the violation is publishing one **without** a finding, or quietly raising the ceiling so a dose passes. |
| **Fix** | Split into two checks: (1) **ceiling integrity** — the reported ceiling must equal the table-derived value for the recorded band; (2) **no silent overdose** — an over-ceiling dose must carry a `DOSE_CEILING` finding. |
| **Invariant gap** | INV-002 said "no output may assert a dose above the ceiling", which is unimplementable. Restated as the two properties above — both testable, both zero-tolerance. |

---

## BUG-0006 — the perception layer imported the judgement layer

| Field | Value |
|---|---|
| **Symptom** | `test/offline/test_structure.py::test_no_authority_import` failed: `extractor/llm.py imports 'adjudicator'`. |
| **Reproduction** | Structural tier, first run. |
| **Classification** | Architecture erosion — a boundary crossing that would have been invisible in review. |
| **Found by** | Architectural fitness function, not a human. |
| **Root cause** | The LLM adapter called `guard.check_payload()` before building its record. Convenient, and a direct violation of "perception must not see the judgement machinery": a model-adjacent module that imports the adjudicator can, in principle, be steered into talking about it. |
| **Fix** | Removed the import. The guard already exists at the contract level (`ExtractionRecord.from_payload` → `_assert_no_authority`), so the adapter keeps the protection without the dependency. |
| **Invariant gap** | INV-003 was tested behaviourally (a payload with a verdict is refused) but not structurally (nothing in the perception path may even *link* to the adjudicator). Both tests now exist. |

---

## BUG-0007 — our own evaluation set carried a patient identifier

| Field | Value |
|---|---|
| **Symptom** | `test_no_real_identifiers_in_fixtures` failed: `c25_approve_with_pii.json: hkid, phone`. |
| **Reproduction** | Full offline suite after the evaluation set was grown from 6 to 25 cases. |
| **Classification** | Repository hygiene — a security rule violated by the team that wrote the rule. |
| **Found by** | REQ-S-001's own gate (`test/offline/test_dependencies.py`), against a fixture written an hour earlier. |
| **Root cause** | The case was added to prove end-to-end masking, and the shortest way to prove it was to commit a note containing an identifier-shaped string. The rule said "fixtures are synthetic and contain no identifiers"; the intent was "no *real* identifiers", and that gap was enough. |
| **Fix** | Fixture deleted. The PHI path is proven in-process in `test_privacy.py::test_outbound_payload_has_no_identifier` — the note is built in memory, the outbound payload is inspected, and the verdict is asserted to be the one the drugs earn. A replacement fixture (`c25_hold_qt_pair.json`) keeps the set at 25 with no PHI. |
| **Invariant gap** | INV-004 was tested as "masking works", not as "no repository artefact ever carries an identifier". Those are different claims, and only the second one survives a reviewer opening the fixtures directory. |
