"""INV-004 (REQ-I-004) — PHI containment."""

from __future__ import annotations

import logging

import pytest

from medcheck.contracts import MaskingError
from medcheck.pipeline import process_case
from medcheck.privacy.mask import Scrubber, find_identifiers, mask

NOTE = (
    "Patient: Chan Tai Man. HKID A123456(3). Phone 9123 4567. DOB 01/02/1970. "
    "Warfarin 5 mg once daily. eGFR 90."
)


def test_identifiers_masked():
    """INV-004: every identifier shape in the note is replaced by a typed token."""
    masked = mask(NOTE)
    for raw in ("Chan Tai Man", "A123456(3)", "9123 4567", "01/02/1970"):
        assert raw not in masked.text, f"raw identifier survived: {raw}"
    assert "‹NAME_1›" in masked.text
    assert find_identifiers(masked.text) == []


def test_mask_roundtrip():
    """INV-004: masking is reversible inside the process, so review is possible."""
    masked = mask(NOTE)
    restored = masked.unmask(masked.text)
    assert restored == NOTE


def test_outbound_payload_has_no_identifier(tables):
    """INV-004: what reaches the extractor contains no identifier."""
    captured: dict[str, str] = {}

    def spy(text: str, vocabulary):
        captured["text"] = text
        from medcheck.extractor import heuristic

        return heuristic.extract(text, vocabulary)

    outcome = process_case({"case_id": "phi", "note": NOTE}, tables=tables, extractor=spy)
    assert find_identifiers(captured["text"]) == []
    assert "Chan" not in captured["text"]
    # The verdict is the one the drugs earn: masking must not change the medicine.
    from medcheck.contracts import Verdict

    assert outcome.verdict is Verdict.APPROVE, outcome.result.to_dict()


def test_masking_failure_blocks_the_call(tables):
    """[INV-004] P-20/P-21: an identifier shape we cannot classify blocks instead of leaking."""
    note = "Patient: A1234567 reviewed. Warfarin 5 mg once daily."
    with pytest.raises(MaskingError):
        mask(note, strict=True)


def test_logs_contain_no_raw_identifier():
    """INV-004: the log scrubber removes identifiers before the record is written."""
    scrubber = Scrubber()
    record = {"case": "HKID A123456(3) phone 9123 4567 on 01/02/1970"}
    scrubbed = scrubber.scrub_record(record)
    assert find_identifiers(str(scrubbed["case"])) == []
    assert scrubber.hits >= 3


def test_scrubber_is_attached_to_root_logger(caplog):
    """[REQ-I-004] A logging handler that uses the scrubber never emits a raw identifier."""
    scrubber = Scrubber()

    class ScrubbingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            record.msg = scrubber.scrub(record.getMessage())

    logger = logging.getLogger("medcheck.test")
    logger.handlers = [ScrubbingHandler()]
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO, logger="medcheck.test"):
        logger.info("case for A123456(3)")

    assert all("A123456" not in record.getMessage() for record in caplog.records)
