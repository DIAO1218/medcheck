# REQ-F-004: Enforce maximum daily dose incl. renal adjustment band.
import json
import pytest
from pathlib import Path
from medcheck.pipeline import process_case

CASES_FILE = Path(__file__).parent.parent / "fixtures" / "supplemental" / "m4_dose_cases.json"

def load_m4_cases():
    if not CASES_FILE.exists():
        return []
    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    return data.get("cases", [])

@pytest.mark.parametrize("case", load_m4_cases(), ids=lambda c: c["case_id"])
def test_m4_supplemental_cases(case):
    """REQ-F-004: Verify M4's supplemental split-dose and unit-conversion cases."""
    note = case["note"]
    expected_verdict = case["expected_verdict"]
    expected_codes = case.get("expected_codes", [])
    
    # Run the pipeline
    outcome = process_case({"case_id": case["case_id"], "note": note})
    
    # Assert the final verdict (APPROVE, HOLD, BLOCK)
    assert outcome.verdict.value == expected_verdict, f"Expected {expected_verdict} for case {case['case_id']} but got {outcome.verdict.value}"
    
    # Assert required finding codes are present
    for code in expected_codes:
        assert code in outcome.result.codes, f"Expected code {code} in findings for case {case['case_id']}"
