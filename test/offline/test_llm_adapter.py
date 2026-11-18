import pytest
from medcheck.contracts import ExtractionRecord, AuthorityViolation

def test_nested_authority_field_rejected():
    """REQ-I-003: Model must not write authority fields at any depth."""
    bad_payload = {"medications": [{"name_raw": "华法林", "meta": {"verdict": "APPROVE"}}]}
    with pytest.raises(AuthorityViolation):
        ExtractionRecord.from_payload(bad_payload, prompt_version="v1.1")

def test_top_level_authority_rejected():
    """REQ-I-003: Model must not supply verdict."""
    bad_payload = {"verdict": "APPROVE", "medications": [{"name_raw": "华法林"}]}
    with pytest.raises(AuthorityViolation):
        ExtractionRecord.from_payload(bad_payload, prompt_version="v1.1")
