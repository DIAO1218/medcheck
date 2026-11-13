# Runtime Policy Catalog

What the system **does** on every degraded or failure path. Each row is a decision already made — no row may be resolved at runtime by judgement, and no row may result in a silent `APPROVE`.

**Global rule:** when in doubt, the case is held for human review. A held case costs a reviewer 60 seconds; a wrong approve costs a patient. Every policy below is an instance of that asymmetry (driver D1).

---

## 1. Ingestion and extraction paths

| # | Trigger | Detection | Policy | User-visible state | Telemetry |
|---|---|---|---|---|---|
| P-01 | Model endpoint unreachable / 5xx after 2 retries with jitter | HTTP status, timeout 8 s | Do **not** fall back to best-effort guessing. Use `extractor.heuristic` if `MEDCHECK_ALLOW_HEURISTIC=1` (offline/dev only), otherwise `HOLD / EXTRACTION_UNAVAILABLE` | verdict `HOLD`, finding `EXTRACTION_UNAVAILABLE`, advisory: "manual review required — extraction service unavailable" | `extractor.failure.count{reason=http}` |
| P-02 | Model returns malformed JSON (3 attempts) | schema validation | One repair attempt with the error appended; if still invalid → `HOLD / EXTRACTION_INVALID`; raw text is logged **hashed only** | `HOLD`, no findings beyond `EXTRACTION_INVALID` | `extractor.invalid.count` |
| P-03 | Model returns a verdict / severity / dose field (INV-003) | `guard.check_authority()` | Abort case with `AuthorityViolation`; do not salvage the rest of the payload. Incident filed | `HOLD / AUTHORITY_VIOLATION`, reviewer sees "model attempted to assert authority — logged as P1" | `authority_violation.count` |
| P-04 | Case note exceeds extraction budget (L6 > 600 tokens) | context assembler | Reject with `CASE_TOO_LARGE`; **never truncate clinical text** (silent truncation could drop a drug) | `HOLD / CASE_TOO_LARGE`, reviewer asked to split the note | `extractor.too_large.count` |
| P-05 | No medication detected | extraction record has empty `medications` | `HOLD / NO_MEDICATIONS_FOUND` (not `APPROVE` — absence of evidence is not evidence of safety) | `HOLD`, advisory asks reviewer to confirm the note contains a prescription | `extraction.empty.count` |
| P-06 | Field present but unparseable ("1 tab" with no strength) | parser returns `unparsed` | Keep the field as `unparsed`, raise `HOLD / FIELD_UNPARSED` naming the field; the drug is still checked against DDI | `HOLD` + finding per unparsed field | `extraction.unparsed.count{field=}` |

## 2. Rule-table paths

| # | Trigger | Detection | Policy | User-visible state | Telemetry |
|---|---|---|---|---|---|
| P-07 | Drug absent from tables (INV-001) | coverage lookup miss | `HOLD / COVERAGE_GAP` naming the drug; no guessing from name similarity | `HOLD` + `COVERAGE_GAP` | `coverage_gap.count` — rate > 20% opens a table sprint |
| P-08 | Pair absent although both drugs known | pair matrix miss | `HOLD / COVERAGE_GAP` naming the pair | `HOLD` + `COVERAGE_GAP` | `coverage_gap.pair.count` |
| P-09 | Table files fail schema/checksum validation at load | loader validates `table_version` + SHA-256 | **Refuse to start.** No partial table load; exit code 3 | process does not start; CLI prints `TABLE_INVALID` | startup failure (blocking) |
| P-10 | Table version differs from the one recorded in the case's resume state | version comparison | Discard in-flight adjudication, re-run from the deterministic core with the new version, append a new audit record marked `supersedes=<old_record_id>` | result reflects new table; audit shows the supersession | `table.version.changed.midflight.count` |
| P-11 | Unit not in the conversion table ("2 puffs", "1 vial") | `rules.units` raises `UnconvertibleUnit` | Do not assume; `HOLD / UNIT_UNSUPPORTED` and skip the dose-ceiling check **for that drug only**, while still running DDI on it | `HOLD` + `UNIT_UNSUPPORTED` | `units.unconvertible.count` |
| P-12 | eGFR required by the drug but absent from the note | dose table marks `renal_sensitive` | `HOLD / RENAL_DATA_MISSING`; apply the most conservative band for the *ceiling comparison* but still hold (never approve on assumed function) | `HOLD` + `RENAL_DATA_MISSING` | `renal.missing.count` |

## 3. Adjudication and output paths

| # | Trigger | Detection | Policy | User-visible state | Telemetry |
|---|---|---|---|---|---|
| P-13 | Finding cannot resolve its `rule_id` (INV-005) | resolution check before emission | Abort with `UnresolvableFinding`; emit nothing | CLI exit 3, `UNRESOLVABLE_FINDING` | `unresolvable_finding.count` (must be 0) |
| P-14 | Asserted dose above ceiling (INV-002) | post-assembly assertion | Abort with `CeilingAssertionError`; **never** publish a partial result | CLI exit 3, `CEILING_ASSERTION` | `ceiling_violations` (release blocker) |
| P-15 | Renderer produces a statement not traceable to a finding/template | conformance check at render time | Drop the statement, log `renderer.conformance.drop`, and if > 0 statements dropped → `HOLD / ADVISORY_INCOMPLETE` | advisory may be shorter; verdict unchanged by rendering | `renderer.conformance.dropped` |
| P-16 | Advisory exceeds 200 words (REQ-Q-002) | word count | Truncate at the last complete finding sentence; never truncate mid-sentence | advisory shorter, verdict unchanged | `advisory.overlength.count` |
| P-17 | Audit append fails (disk full, lock timeout) | IOError | **Do not deliver the result.** Retry twice, then fail the case with `AUDIT_UNAVAILABLE` | CLI exit 4, no result document | `audit.failure.count` (P1) |
| P-18 | Two adjudications for the same `case_id` | unique constraint | Reject the second with `DUPLICATE_CASE`; reviewer must use the override path | CLI exit 2, `DUPLICATE_CASE` | `duplicate_case.count` |
| P-19 | Human override recorded on a `BLOCK` verdict | override API | Override is allowed **only** with reviewer id + free-text rationale ≥ 20 chars; original verdict stays in the audit record, override is a separate appended record | result shows `overridden_by`, verdict unchanged in history | `override.count`, `override.on_block.count` |

## 4. Privacy paths

| # | Trigger | Detection | Policy | User-visible state | Telemetry |
|---|---|---|---|---|---|
| P-20 | Masking finds a pattern it cannot classify (e.g. an unfamiliar ID format) | masker `unclassified_identifier` | Block the model call with `MaskingError`; hold the case | `HOLD / MASKING_UNCERTAIN` | `masking.uncertain.count` |
| P-21 | Outbound payload contains a residual identifier | pre-flight scan of the payload | Block transmission, then re-mask and retry once; on second hit, abandon | `HOLD / PHI_LEAK_BLOCKED` | `phi_leak_blocked.count` (P1) |
| P-22 | Log record contains a raw identifier | log `Scrubber` | Scrubber redacts in place and increments a counter; the raw record is never written | invisible to user | `privacy.scrub.hits` (must be 0) |

## 5. Degraded-mode summary

| Mode | Verdict outcome | Permitted? |
|---|---|---|
| No model available, heuristic extractor enabled (dev/CI only) | whatever the deterministic core concludes from heuristic extraction | dev/CI yes; production no (`MEDCHECK_ALLOW_HEURISTIC` must be unset) |
| No model available, no heuristic | `HOLD` | yes |
| Unknown coverage | `HOLD` | yes |
| Any invariant assertion fires | no output at all | yes (this is the designed failure) |
| Any path that would yield `APPROVE` without a coverage proof | does not exist | — |

**Non-negotiable:** there is no configuration flag that turns a `HOLD` into an `APPROVE`, and no environment variable that disables an invariant. The only switches in the system are `MEDCHECK_ALLOW_HEURISTIC` (dev/CI), `MEDCHECK_RENDERER` (template|llm), and `MEDCHECK_LOG_LEVEL` — none of them touches adjudication.
