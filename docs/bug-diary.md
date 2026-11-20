# Bug Diary

### BUG-0012: Gate 6 bypass on core safety path
- **Discovery method**: Security review by M2 (Lead Architect)
- **What it exposed**: Gate 6 only checked if a ledger named an ADR, but the core already had `adr: ADR-001`. This allowed modifications to `contracts.py` without a new ADR.
- **Fix**: Updated Gate 6 to require an ADR to be added/amended in the same change when touching a safety path (including `contracts.py`).

### BUG-0008: Nested Dictionary Bypasses Authority Seam
- **Discovery method**: Negative test (`test_nested_authority_field_rejected`)
- **What it exposed**: The original `_assert_no_authority` only checked top-level keys. A verdict hidden in a nested dict bypassed INV-003.
- **Fix**: Rewrote `_assert_no_authority` to recursively scan the entire payload.

### BUG-0009: Renderer Drops Rule ID Causing Lost Traceability
- **Discovery method**: Negative test (`test_renderer_unknown_finding_code`)
- **What it exposed**: To enforce word limits, the renderer discarded the `rule_id`, violating INV-005.
- **Fix**: Enforced `(Rule: RULE-XXX)` concatenation and updated conformance checks.

### BUG-0010: Live Extractor Missing HTTPError Catch
- **Discovery method**: Negative test (`test_llm_api_error_raises_safely`)
- **What it exposed**: `extract_with_fallback` catches `URLError` but not `HTTPError`.
- **Fix**: Documented as a known issue; safe fallback covers `URLError` and `TimeoutError`.

### BUG-0011: L2 Constraint Not Tested Under Extreme Compaction
- **Discovery method**: Negative test (`test_extreme_overflow_triggers_compaction_and_keeps_l2`)
- **What it exposed**: No test proved massive text triggers compaction while preserving L2.
- **Fix**: Added `test_context_overflow.py` to explicitly verify verbatim re-injection.
