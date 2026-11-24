# Transcript: M3 Hardening of Extractor, Prompt, and Renderer Boundaries

**Date**: 2026-11-18
**Agent Role**: M3 Build Lead A (Extraction, Prompt, Rendering)
**AI Collaborator**: Claude 3.5 Sonnet
**Provenance**: Reconstructed from build logs, bug diary, and live session records.

---

## 1. Task Declaration
As Build Lead A, the primary objectives for this session were:
1. Harden the authority seam of `ExtractionRecord` (prevent nested authority bypass by the model).
2. Verify the "bulletproof" nature of Context Assembly (L2 constraints) under extreme long-text compaction.
3. Ensure the Renderer preserves traceability (Rule ID) and does not hallucinate numbers.

## 2. Key Human Interventions and Corrections

### Intervention 1: Catching an AI Factual Error in Test Assertions (CORRECT)
- **Context**: The AI generated the `test_llm_fallback_appends_trace` test, asserting the heuristic fallback version was `"heuristic-v1.0"`.
- **Human Discovery**: Ran the test locally, which failed (`assert 'heuristic-v1' == 'heuristic-v1.0'`).
- **Correction**: Did not blindly trust the AI's code. Cross-checked the source code, found the actual version string was `"heuristic-v1"`, manually fixed the test, and re-ran it to green.
- **Significance**: Proved that the human reviewer did not treat the AI as an "authority". Instead, they used the failing test to expose a hallucinated field.

### Intervention 2: Fixing the Nested Dictionary Authority Bypass (REJECT & REDIRECT)
- **Context**: The AI provided an initial negative test, exposing that `_assert_no_authority` in `contracts.py` only checked top-level keys. The model could bypass the safety seam via `{"meta": {"verdict": "APPROVE"}}`.
- **Human Decision**: Directed the AI to provide a recursive scanning solution, modified the source code, and fixed a concurrency bug in the renderer where concatenating `(Rule: ...)` caused number misjudgments.
- **Significance**: This was the most valuable discovery of the session. The human not only had the AI fix the logic but also required it to update `bug-diary.md` (BUG-0008, BUG-0009).

### Intervention 3: Navigating CI Static Analysis Gates (REDIRECT)
- **Context**: After pushing the code to GitHub, Gate 2 (Static Analysis) reported 14 errors, and Gate 5 (Regression) failed due to missing requirement declarations.
- **Human Intervention**: Ran `ruff check . --fix` locally and manually fixed unused pytest imports and test docstring requirement references.
- **Significance**: The AI could not directly access the GitHub CI environment. The human used the error logs to guide the AI in completing the final formatting alignment.

## 3. Core Outputs and Verification
- Modified `src/medcheck/contracts.py` to reject authority fields at any depth.
- Modified `src/medcheck/renderer/template.py` to enforce traceable `(Rule: RULE-XXX)` rendering.
- Added 4 offline negative tests, fully verified via `pytest`.
- Implemented a "shadow evaluation" for the live model response path via mocking, advancing the closure of DEBT-06.

## 4. Reflection
The AI demonstrated high efficiency in code generation during this session. However, when dealing with **safety assertions** and **engineering constraints (e.g., lint, version alignment)**, it was prone to subtle hallucinations or execution deviations. The value of human supervision lies in: **not treating the AI as a "verifier," but as a "generator," and ruthlessly falsifying it using tests and CI gates.**
