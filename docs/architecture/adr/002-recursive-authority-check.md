# ADR 002: Recursive Authority Check in the Contract

## Context
During a security audit and negative testing (see BUG-0008), we discovered that the `ExtractionRecord.from_payload` method in `src/medcheck/contracts.py` only checked for forbidden authority fields (e.g., `verdict`, `severity`) at the top level of the payload. If the model hid an authority field inside a nested dictionary (e.g., `{"medications": [{"meta": {"verdict": "APPROVE"}}]}`), it would silently bypass the authority seam, violating INV-003.

## Decision
We amended `_assert_no_authority` to perform a recursive scan over the entire payload (including nested dictionaries and lists). This ensures that no matter where the model hides an authority field, the entire payload is rejected.

## Rationale
The fix belongs in the contract layer, not the guard or adjudicator. The contract is the first line of defense (the data structure itself). If we allowed nested fields to bypass the contract, the guard would have to know about arbitrary data shapes. By rejecting the payload at the boundary, we enforce the principle that "partial trust is not trust."

## Consequences and Revisit Conditions
- **Positive**: The system is now immune to nested authority injection attempts.
- **Negative**: Slightly more CPU cycles for recursive scanning (negligible for clinical notes).
- **Revisit if**: The payload schema becomes so deeply nested that recursive scanning causes performance issues, or if a new authority field type is introduced that requires a different traversal mechanism.
