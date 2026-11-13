# Memory and State Design

Two different memories exist in this project and they must not be confused:

- **System memory** — state the *application* keeps between cases, sessions, and versions (this document, §1–§5).
- **Agent memory** — state the *coding agent* keeps between sessions so a supervised build can be resumed (this document, §6).

Mixing them is a documented hazard: agent session notes leaking into the audit log would violate INV-004, and application PHI leaking into agent memory would violate it twice.

---

## 1. State inventory

| # | State | Lives where | Survives session? | Survives interruption mid-case? | Survives version change? | Owner |
|---|---|---|---|---|---|---|
| S1 | Rule tables (units, DDI, dose, renal bands) | `data/rules/*.yaml`, pinned by `table_version` | yes | yes | **no** — version is explicit and immutable per release | human reviewer |
| S2 | Audit records | `data/audit/audit.jsonl` (append-only, hash-chained) | yes | yes | yes — never rewritten | `audit` component |
| S3 | Case-in-progress state (partial extraction, open questions) | `data/state/<case_id>.json`, TTL 24 h | yes | yes (resume point) | yes | `extractor` |
| S4 | Extraction cache (masked note hash → record) | `data/cache/extraction/`, TTL 7 d | yes | n/a | **invalidated** on prompt version change | `extractor` |
| S5 | Coverage-gap telemetry | `data/telemetry/coverage-gaps.jsonl` | yes | yes | yes | `adjudicator` |
| S6 | Human override decisions | inside the audit record (S2), never a separate store | yes | yes | yes | reviewer |
| S7 | Semantic evaluation results | `docs/architecture/evaluation-logbook.md` + `data/eval/runs/<date>.json` | yes | n/a | yes | verify role |
| S8 | Agent session state (plan, approved tests, open questions) | `.workbuddy/memory/` + `transcripts/` | yes | n/a | n/a | human |

## 2. What must never be stored

| Forbidden | Why | Enforcement |
|---|---|---|
| Raw case text in any log or audit record | INV-004 | `Scrubber` on log handlers; audit stores `input_hash` (SHA-256 of masked text), never text |
| Raw identifiers in `data/state` | INV-004 | state file stores masked tokens only; `test_privacy.py` inspects the state dir |
| Model output quoted into audit as authoritative | INV-003 | audit record stores findings + verdict only, plus `prompt_version` |
| Unmasked note in `data/cache` | INV-004 | cache key is the hash of the *masked* text; value is the extraction record |
| Anything in git under `data/` | REQ-S-001 | `.gitignore` excludes `data/` except `data/rules/`; CI checks |

## 3. Write policy

| Store | Written by | When | Idempotent? |
|---|---|---|---|
| S1 tables | human only, via PR + schema gate | release | n/a (versioned files) |
| S2 audit | `audit.append()` only | once per adjudicated case, last step before result emission | no — append always creates a record; duplicate `case_id` is rejected |
| S3 state | `extractor` | after each turn that changes the extraction | yes — last write wins per `case_id` |
| S4 cache | `extractor` | after schema-valid extraction | yes — key includes prompt version |
| S5 telemetry | `adjudicator` | on `COVERAGE_GAP` or ceiling assertion | no (append) |
| S6 override | reviewer via CLI | after human review | no (append; latest wins on read) |
| S7 eval | `scripts/eval_replay.py` | on prompt/model change | yes — one run file per `(date, prompt_version)` |

**Ordering rule:** audit append happens *after* the verdict is fixed and *before* the result is returned. A crash between the two yields a record with no delivered result — acceptable (orphan record, reconciled by `audit.reconcile()`). The reverse (delivered result without a record) is unacceptable, because it would be an unaudited safety decision.

## 4. Retrieval policy

| Query | Source | Rule |
|---|---|---|
| "Why was this case blocked?" | S2 by `case_id` | exact match only; returns findings + `rule_id` + `table_version` |
| "Which table version produced this verdict?" | S2 | field, not a join |
| "Has this drug been seen as a gap before?" | S5 | last 90 days, grouped by canonical name |
| "Resume an interrupted case" | S3 | only within TTL; expired state is discarded, not resurrected |
| "Was this extraction already computed?" | S4 | key exact match on (masked hash, prompt version) — a miss is a normal recompute |

No semantic/vector retrieval over audit data. Reasoned in `option-ledger.md` (O-4): embedding patient case text would create a second, unaudited copy of PHI.

## 5. Retention and privacy

| Store | Retention | Deletion |
|---|---|---|
| S2 audit | duration of the course + 1 semester (teaching portfolio) | end-of-course wipe script, recorded in `docs/review-memo.md` |
| S3 state | 24 h TTL, swept on process start | automatic |
| S4 cache | 7 d TTL | automatic |
| S5 telemetry | 90 d rolling | automatic |
| S7 eval runs | permanent (aggregate scores only, no case text) | n/a |
| Fixtures | permanent, synthetic only | n/a |

**Privacy posture:** the audit record is *pseudonymous* — `case_id` is a random UUID, `input_hash` is a hash of masked text, and no identifier field exists in the schema. Re-identification requires the original note, which is never stored by this system. Retention of S2 is justified by auditability (REQ-F-007), and the tradeoff is recorded here rather than left implicit.

## 6. Agent session state (the coding agent's memory)

| Item | Location | Write policy |
|---|---|---|
| Execution plan awaiting approval | `transcripts/<id>-<name>.md` (session log) | agent writes the plan, human records approval inline |
| Approved test list for a change | `transcripts/`, PR template checkbox | human-only confirmation |
| Open questions / blockers | `.workbuddy/memory/YYYY-MM-DD.md` | agent appends; no PHI, no case text |
| Architecture decisions | `docs/architecture/adr/` | human-only commit |
| Debt noticed mid-build | `docs/debt-register.md` | agent may append a row, human triages |

**Freshness rule** (`.agent/rules.md`): if a requirement changes, the affected rules and `AGENTS.md` must be updated within one sprint. Staleness is detected by comparing the registry `last_updated` with the last commit touching `AGENTS.md`; if the gap exceeds one sprint, the debt register gains a `prompt rot` entry and the next PR is blocked until refreshed.

**Resumption protocol:** on a new session the agent reads, in order, `AGENTS.md` → `architecture-blueprint.md` → the current sprint's `transcripts/` entry → `docs/debt-register.md`. It must state what it believes the current task is and wait for confirmation before writing code. This is the mechanism that makes a 5-transcript pipeline coherent rather than five unrelated sessions.
