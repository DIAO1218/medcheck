"""Advisory renderer. A terminal sink: nothing downstream reads its output.

Decision: ADR-001 section 2 (the model may paraphrase, never decide).
Requirement: REQ-F-006 (every statement traces to a finding).

Every sentence must be traceable to a finding or to a fixed template id, because
prose that can introduce a new claim is prose that can contradict the verdict
(REQ-F-006). The renderer may use a model later; the conformance check does not
care which, only that the words came from the adjudication.
"""

from __future__ import annotations

import re
from ..contracts import AdjudicationResult, Finding

MAX_WORDS = 200
TPL_HEADER = "TPL-HEADER"
TPL_FOOTER = "TPL-FOOTER"

def header(result: AdjudicationResult) -> str:
    return f"{result.verdict.value} FOR REVIEW — NOT FOR CLINICAL USE"

def footer(result: AdjudicationResult) -> str:
    coverage = "complete" if result.coverage_complete else "incomplete"
    return f"Evaluated against rule table {result.table_version}; coverage {coverage}."

def _sentence(finding: Finding) -> str:
    severity = finding.severity.value
    body = finding.statement.rstrip(".")
    return f"[{severity}] {body} (Rule: {finding.rule_id})."

def finding_statements(result: AdjudicationResult) -> list[tuple[str, str]]:
    """(sentence, source ref) pairs. The ref is a rule id; no free text here."""
    out: list[tuple[str, str]] = []
    for finding in result.findings:
        out.append((_sentence(finding), finding.rule_id))
    return out

def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))

def _cap_words(text: str) -> str:
    words = text.split()
    if len(words) <= MAX_WORDS:
        return text
    kept: list[str] = []
    count = 0
    for line in text.splitlines():
        line_words = len(line.split())
        if count + line_words > MAX_WORDS - 12:
            break
        kept.append(line)
        count += line_words
    return "\n".join(kept)

def render(result: AdjudicationResult) -> str:
    lines = [header(result)]
    lines.extend(text for text, _ in finding_statements(result))
    lines.append(footer(result))
    return _cap_words("\n".join(lines))

def conformance_violations(result: AdjudicationResult, text: str) -> list[str]:
    """Return reasons the advisory drifts from the adjudication (empty = clean)."""
    violations: list[str] = []
    allowed_refs = {finding.rule_id for finding in result.findings}
    sentences = [line.strip() for line in text.splitlines() if line.strip()]

    if not sentences or sentences[0] != header(result):
        violations.append("header missing or altered")

    known_numbers = _numbers(" ".join(finding.statement for finding in result.findings))
    for sentence in sentences[1:]:
        if sentence == footer(result):
            continue
        # 忽略 (Rule: XXX) 里包含的编号数字
        clean_sentence = re.sub(r'\(Rule:.*?\)', '', sentence)
        if not re.match(r"^\[(contraindicated|major|moderate|minor|info)\]", sentence):
            violations.append(f"unattributed statement: {sentence[:40]}")
            continue
        
        body = sentence.split("] ", 1)[-1]
        body_without_rule = re.sub(r"\s*\(Rule:.*?\)", "", body).strip()
        
        if body_without_rule.rstrip(".") not in (f.statement.rstrip(".") for f in result.findings if f.rule_id in allowed_refs):
            violations.append(f"statement not derived from a finding: {body[:40]}")
            
        for number in _numbers(clean_sentence):
            if number not in known_numbers:
                violations.append(f"number '{number}' appears in prose but not in any finding")
    return violations
