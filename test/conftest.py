"""Shared fixtures.

The tables are loaded once per session: a test that reloads YAML per case measures
the filesystem, not the adjudicator.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medcheck.contracts import Medication  # noqa: E402
from medcheck.rules.loader import get_tables  # noqa: E402


@pytest.fixture(scope="session")
def tables():
    return get_tables()


@pytest.fixture
def med():
    """Build a Medication with sensible defaults."""

    def _build(name: str, value: float | None = 5.0, unit: str | None = "mg", freq: str | None = "once daily") -> Medication:
        return Medication(
            name_raw=name.title(),
            name_canonical=name,
            dose_value=value,
            dose_unit=unit,
            frequency_text=freq,
        )

    return _build


@pytest.fixture
def repo_root() -> Path:
    return ROOT
