import re
from medcheck.contracts import AdjudicationResult, Finding, Severity, Verdict
from medcheck.renderer import template

def test_renderer_unknown_finding_code():
    """REQ-F-006: Advisory prose must retain rule_id for traceability."""
    result = AdjudicationResult(
        case_id="test-case", verdict=Verdict.HOLD,
        findings=(Finding(rule_id="RULE-999", code="UNKNOWN_SECRET_CODE", severity=Severity.MAJOR, statement="Something weird happened.", table_version="v1.0"),),
        coverage_complete=True, table_version="v1.0"
    )
    advisory = template.render(result)
    assert "RULE-999" in advisory
    assert "Something weird happened" in advisory

def test_renderer_introduces_no_new_numbers():
    """REQ-F-006: Renderer must not introduce new numeric claims."""
    result = AdjudicationResult(
        case_id="test-case", verdict=Verdict.HOLD,
        findings=(Finding(rule_id="RULE-001", code="COVERAGE_GAP", severity=Severity.MAJOR, statement="No interaction data available.", table_version="v1.0"),),
        coverage_complete=False, table_version="v1.0"
    )
    advisory = template.render(result)
    clean_advisory = re.sub(r'\(Rule:.*?\)', '', advisory)
    numbers = re.findall(r'\d+(?:\.\d+)?', clean_advisory)
    unexpected_numbers = [n for n in numbers if n not in ["1", "1.0", "200"]]
    assert not unexpected_numbers, f"Renderer invented numbers: {unexpected_numbers}"
