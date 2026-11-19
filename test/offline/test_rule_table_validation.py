"""REQ-F-002 / REQ-F-003 / REQ-F-004: reject invalid authoritative rule tables."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from medcheck.contracts import TableInvalid
from medcheck.rules.loader import REQUIRED_FILES, load_tables

RULES = Path(__file__).resolve().parents[2] / "data" / "rules"


def _rule_copy(tmp_path: Path) -> Path:
    for filename in REQUIRED_FILES:
        shutil.copy2(RULES / filename, tmp_path / filename)
    return tmp_path


def _mutate(tmp_path: Path, filename: str, mutation: str) -> Path:
    rules_dir = _rule_copy(tmp_path)
    path = rules_dir / filename
    document: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))

    if mutation == "zero_conversion":
        document["conversions"]["mg"] = 0.0
    elif mutation == "negative_frequency":
        document["frequencies"]["once daily"] = -1.0
    elif mutation == "unknown_severity":
        row = next(item for item in document["interactions"] if item["rule_id"] == "DDI-007")
        row["severity"] = "contraindcated"
    elif mutation == "zero_ceiling":
        document["drugs"]["warfarin"]["max_mg_per_day"] = 0.0
    elif mutation == "negative_renal_factor":
        document["renal_bands"][0]["factor"] = -0.25
    elif mutation == "duplicate_renal_threshold":
        document["renal_bands"][1]["max_egfr"] = document["renal_bands"][0]["max_egfr"]
    else:  # pragma: no cover - protects the test helper itself
        raise AssertionError(f"unknown mutation: {mutation}")

    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return rules_dir


@pytest.mark.parametrize(
    ("filename", "mutation"),
    [
        ("units.yaml", "zero_conversion"),
        ("units.yaml", "negative_frequency"),
        ("ddi.yaml", "unknown_severity"),
        ("dose.yaml", "zero_ceiling"),
        ("dose.yaml", "negative_renal_factor"),
        ("dose.yaml", "duplicate_renal_threshold"),
    ],
    ids=[
        "zero-unit-conversion",
        "negative-frequency",
        "unknown-interaction-severity",
        "zero-dose-ceiling",
        "negative-renal-adjustment",
        "duplicate-renal-boundary",
    ],
)
def test_invalid_rule_tables_are_rejected(tmp_path, filename, mutation):
    """REQ-F-002 / REQ-F-003 / REQ-F-004: invalid safety tables must fail closed."""
    rules_dir = _mutate(tmp_path, filename, mutation)

    with pytest.raises(TableInvalid):
        load_tables(rules_dir)


def test_current_rule_tables_load_successfully(tmp_path):
    """REQ-F-002 / REQ-F-003 / REQ-F-004: the valid pinned tables remain loadable."""
    rules_dir = _rule_copy(tmp_path)

    tables = load_tables(rules_dir)

    assert tables.interactions
    assert tables.drugs
    assert tables.renal_bands
