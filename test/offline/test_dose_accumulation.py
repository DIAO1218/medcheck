"""REQ-F-004 / INV-002: total independent schedules for the same medication."""

import pytest

from medcheck.contracts import CODE_DOSE_CEILING, CODE_UNIT_UNSUPPORTED, ExtractionRecord, Verdict
from medcheck.pipeline import process_case
from medcheck.rules import dose


@pytest.mark.parametrize("per_dose", [4.0, 5.0, 6.0])
def test_split_schedule_has_one_daily_total(med, tables, per_dose):
    """REQ-F-004 / INV-002: separate schedules share one daily ceiling."""
    medications = [
        med("warfarin", per_dose, freq="mane"),
        med("warfarin", per_dose, freq="nocte"),
    ]
    result = dose.check(medications, egfr=None, tables=tables)

    assert len(result.normalized) == 1
    total = result.normalized[0]
    assert total.mg_per_day == pytest.approx(per_dose * 2)
    assert total.ceiling_mg_per_day == 10.0
    expected = [CODE_DOSE_CEILING] if per_dose > 5 else []
    assert [finding.code for finding in result.findings] == expected


def test_split_schedule_converts_units_before_summing(med, tables):
    """REQ-F-002 / REQ-F-004: accumulate normalized quantities, not raw numbers."""
    medications = [
        med("warfarin", 0.006, unit="g", freq="mane"),
        med("warfarin", 6000.0, unit="mcg", freq="nocte"),
    ]
    result = dose.check(medications, egfr=None, tables=tables)

    assert len(result.normalized) == 1
    assert result.normalized[0].mg_per_day == pytest.approx(12.0)
    assert [finding.code for finding in result.findings] == [CODE_DOSE_CEILING]


def test_different_drugs_do_not_share_a_daily_total(med, tables):
    """REQ-F-004: the accumulation key is the canonical medication name."""
    result = dose.check(
        [med("warfarin", 6.0), med("omeprazole", 20.0)],
        egfr=None,
        tables=tables,
    )

    assert {item.medication: item.mg_per_day for item in result.normalized} == {
        "warfarin": 6.0, "omeprazole": 20.0,
    }
    assert result.findings == []


def test_split_schedule_uses_renal_adjusted_total_ceiling(med, tables):
    """REQ-F-004 / INV-002: renal adjustment applies once to the combined total."""
    result = dose.check(
        [med("metformin", 700.0, freq="mane"), med("metformin", 700.0, freq="nocte")],
        egfr=25.0,
        tables=tables,
    )

    assert len(result.normalized) == 1
    total = result.normalized[0]
    assert total.mg_per_day == 1400.0
    assert total.ceiling_mg_per_day == 1275.0
    assert total.renal_band == "G4"
    assert [finding.code for finding in result.findings] == [CODE_DOSE_CEILING]


def test_pipeline_blocks_preserved_split_schedule(med, tables):
    """REQ-F-004 / INV-002: verify downstream adjudication independently of M3 extraction."""
    record = ExtractionRecord(medications=(
        med("warfarin", 6.0, freq="mane"),
        med("warfarin", 6.0, freq="nocte"),
    ))

    def preserved_extractor(note, vocabulary):
        return record

    outcome = process_case(
        {"case_id": "split-dose-regression", "note": "Warfarin 6 mg mane. Warfarin 6 mg nocte."},
        tables=tables,
        extractor=preserved_extractor,
    )

    assert len(outcome.record.medications) == 2
    assert outcome.verdict is Verdict.BLOCK
    assert outcome.result.codes == [CODE_DOSE_CEILING]


def test_combined_daily_dose_overflow_is_reported(med, tables):
    """REQ-F-004 / INV-002: adding finite schedules must not produce infinity."""
    result = dose.check(
        [med("warfarin", 1e308, freq="mane"), med("warfarin", 1e308, freq="nocte")],
        egfr=None,
        tables=tables,
    )
    assert result.normalized == []
    assert [finding.code for finding in result.findings] == [CODE_UNIT_UNSUPPORTED]


def test_unparsed_schedule_does_not_publish_partial_total(med, tables):
    """REQ-F-004: report an unusable schedule rather than a misleading partial total."""
    result = dose.check(
        [med("warfarin", 5.0, freq="mane"), med("warfarin", 6.0, freq="when required")],
        egfr=None,
        tables=tables,
    )
    assert result.normalized == []
    assert [finding.code for finding in result.findings] == [CODE_UNIT_UNSUPPORTED]


@pytest.mark.parametrize("frequency", ["when required", None])
@pytest.mark.parametrize("reverse", [False, True])
def test_pipeline_holds_preserved_unparsed_schedule(med, tables, frequency, reverse):
    """REQ-F-004: dose uncertainty holds even without an extractor unparsed warning."""
    medications = [
        med("warfarin", 5.0, freq="mane"),
        med("warfarin", 6.0, freq=frequency),
    ]
    if reverse:
        medications.reverse()
    record = ExtractionRecord(medications=tuple(medications))

    def preserved_extractor(note, vocabulary):
        return record

    outcome = process_case(
        {
            "case_id": "split-unparsed-regression",
            "note": "Warfarin 5 mg mane. Warfarin 6 mg when required.",
        },
        tables=tables,
        extractor=preserved_extractor,
    )

    assert len(outcome.record.medications) == 2
    assert outcome.verdict is Verdict.HOLD
    assert outcome.result.codes == [CODE_UNIT_UNSUPPORTED]
