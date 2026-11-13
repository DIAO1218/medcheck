"""REQ-F-004 — maximum daily dose with renal banding."""

from __future__ import annotations

import pytest

from medcheck.contracts import CODE_DOSE_CEILING, CODE_RENAL_DATA_MISSING, CODE_UNIT_UNSUPPORTED
from medcheck.rules import dose
from medcheck.rules.loader import get_tables


def test_over_limit_blocked(med, tables):
    """REQ-F-004: 20 mg/day warfarin is above the 10 mg ceiling."""
    result = dose.check([med("warfarin", 20.0)], egfr=None, tables=tables)
    assert [finding.code for finding in result.findings].count(CODE_DOSE_CEILING) == 1


def test_compliant_not_blocked(med, tables):
    """REQ-F-004: 5 mg/day is inside the ceiling."""
    result = dose.check([med("warfarin", 5.0)], egfr=None, tables=tables)
    assert result.findings == []
    assert result.normalized[0].ceiling_mg_per_day == 10.0


def test_ceiling_is_inclusive(med, tables):
    """[REQ-F-004] Boundary: exactly at the ceiling is allowed, one unit above is not."""
    at_limit = dose.check([med("warfarin", 10.0)], egfr=None, tables=tables)
    above = dose.check([med("warfarin", 10.5)], egfr=None, tables=tables)
    assert at_limit.findings == []
    assert [f.code for f in above.findings] == [CODE_DOSE_CEILING]


def test_renal_band_selected(med, tables):
    """REQ-F-004: eGFR 25 selects G4 (factor 0.5) for a renally cleared drug."""
    result = dose.check([med("metformin", 2000.0)], egfr=25.0, tables=tables)
    normalized = result.normalized[0]
    assert normalized.renal_band == "G4"
    assert normalized.ceiling_mg_per_day == pytest.approx(2550.0 * 0.5)
    assert [f.code for f in result.findings] == [CODE_DOSE_CEILING]


def test_renal_band_g5_is_conservative(med, tables):
    """[REQ-F-004] renal band g5 is conservative."""
    result = dose.check([med("metformin", 700.0)], egfr=10.0, tables=tables)
    assert result.normalized[0].renal_band == "G5"
    assert result.normalized[0].ceiling_mg_per_day == pytest.approx(2550.0 * 0.25)
    assert [f.code for f in result.findings] == [CODE_DOSE_CEILING]


def test_missing_egfr_holds_and_skips_the_ceiling(med, tables):
    """[REQ-F-004] P-12: a renally cleared drug without eGFR is held, not blocked on a guess."""
    result = dose.check([med("digoxin", 0.125)], egfr=None, tables=tables)
    codes = [finding.code for finding in result.findings]
    assert codes == [CODE_RENAL_DATA_MISSING]
    assert result.normalized == []


def test_non_renal_drug_ignores_missing_egfr(med, tables):
    """[REQ-F-004] non renal drug ignores missing egfr."""
    result = dose.check([med("warfarin", 5.0)], egfr=None, tables=tables)
    assert CODE_RENAL_DATA_MISSING not in [f.code for f in result.findings]


def test_unsupported_unit_skips_ceiling_but_is_reported(med, tables):
    """[REQ-F-004] P-11: '2 tab' cannot be normalised, so the ceiling is skipped -- loudly."""
    inhaler = med("warfarin", 2.0, unit="tab")
    result = dose.check([inhaler], egfr=None, tables=tables)
    codes = [finding.code for finding in result.findings]
    assert CODE_UNIT_UNSUPPORTED in codes
    assert result.normalized == []


def test_unknown_drug_is_not_the_dose_modules_job(med, tables):
    """[REQ-F-004] Coverage owns unknown drugs; dose must stay silent rather than invent a ceiling."""
    result = dose.check([med("morphine", 10.0)], egfr=None, tables=tables)
    assert result.findings == []
    assert result.normalized == []


def test_table_version_is_stable_across_loads():
    """INV-005 support: the version is a content hash, not a clock."""
    assert get_tables().version == get_tables().version
