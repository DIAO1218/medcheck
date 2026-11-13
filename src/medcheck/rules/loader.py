"""Rule-table loading and versioning.

Decision: ADR-001 section 2 (versioned tables as the only source of truth).
Invariant: INV-005 (every finding resolves to a pinned table version).

The table version is a content hash, not a handwritten string: two runs with the
same file bytes must report the same version, and any edit must change it
(REQ-I-005 depends on this being impossible to fake).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ..contracts import TableInvalid

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[3] / "data" / "rules"
REQUIRED_FILES = ("units.yaml", "ddi.yaml", "dose.yaml")


@dataclass(frozen=True)
class RuleTables:
    version: str
    canonical_unit: str
    conversions: Mapping[str, float]
    frequencies: Mapping[str, float]
    interactions: tuple[Mapping[str, Any], ...]
    drugs: Mapping[str, Mapping[str, Any]]
    renal_bands: tuple[Mapping[str, Any], ...]
    vocabulary: tuple[str, ...]
    holes: frozenset[frozenset[str]] = frozenset()

    # -- coverage ---------------------------------------------------------- #
    def covers_drug(self, canonical_name: str) -> bool:
        """A drug is covered only if it has a dose row. DDI-only knowledge is
        not enough to approve, because we could not check its ceiling."""
        return canonical_name in self.drugs

    def is_hole(self, first: str, second: str) -> bool:
        """A declared knowledge hole: the pair is *unassessed*, not safe."""
        return frozenset({first, second}) in self.holes

    def covers_pair(self, first: str, second: str) -> bool:
        key = frozenset({first, second})
        return any(frozenset(row["pair"]) == key for row in self.interactions)

    def interaction(self, first: str, second: str) -> Mapping[str, Any] | None:
        key = frozenset({first, second})
        for row in self.interactions:
            if frozenset(row["pair"]) == key:
                return row
        return None

    def dose_row(self, canonical_name: str) -> Mapping[str, Any] | None:
        return self.drugs.get(canonical_name)

    def renal_band(self, egfr: float | None) -> Mapping[str, Any]:
        """Most conservative band wins when eGFR is unknown (P-12)."""
        if egfr is None:
            return min(self.renal_bands, key=lambda band: band["factor"])
        for band in sorted(self.renal_bands, key=lambda item: item["max_egfr"]):
            if egfr <= band["max_egfr"]:
                return band
        return max(self.renal_bands, key=lambda band: band["factor"])


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TableInvalid(f"missing rule table: {path.name}")
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except yaml.YAMLError as exc:  # pragma: no cover - malformed file
        raise TableInvalid(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise TableInvalid(f"{path.name} must contain a mapping")
    return document


def _content_version(documents: Mapping[str, dict[str, Any]]) -> str:
    payload = json.dumps(documents, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    declared = documents["dose.yaml"].get("version", "0")
    return f"{declared}+sha:{digest}"


def load_tables(rules_dir: Path | str | None = None) -> RuleTables:
    directory = Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR
    documents = {name: _read_yaml(directory / name) for name in REQUIRED_FILES}

    for name, document in documents.items():
        if "version" not in document:
            raise TableInvalid(f"{name} has no version")

    units = documents["units.yaml"]
    ddi = documents["ddi.yaml"]
    dose = documents["dose.yaml"]

    for key in ("conversions", "frequencies", "canonical_unit"):
        if key not in units:
            raise TableInvalid(f"units.yaml missing '{key}'")
    for key in ("interactions", "version"):
        if key not in ddi:
            raise TableInvalid(f"ddi.yaml missing '{key}'")
    for key in ("drugs", "renal_bands", "version"):
        if key not in dose:
            raise TableInvalid(f"dose.yaml missing '{key}'")

    interactions = tuple(ddi["interactions"])
    for row in interactions:
        missing = {"rule_id", "pair", "severity"} - set(row)
        if missing:
            raise TableInvalid(f"interaction row missing {sorted(missing)}: {row}")
        if len(row["pair"]) != 2:
            raise TableInvalid(f"interaction pair must have two drugs: {row}")

    drugs = dose["drugs"]
    for name, row in drugs.items():
        missing = {"rule_id", "max_mg_per_day"} - set(row)
        if missing:
            raise TableInvalid(f"dose row for {name} missing {sorted(missing)}")

    vocabulary = tuple(sorted(set(drugs) | {drug for row in interactions for drug in row["pair"]}))

    holes = frozenset(
        frozenset(row["pair"]) for row in ddi.get("coverage_holes", []) if "pair" in row
    )

    return RuleTables(
        version=_content_version(documents),
        canonical_unit=units["canonical_unit"],
        conversions=dict(units["conversions"]),
        frequencies=dict(units["frequencies"]),
        interactions=interactions,
        drugs=dict(drugs),
        renal_bands=tuple(dose["renal_bands"]),
        vocabulary=vocabulary,
        holes=holes,
    )


@lru_cache(maxsize=4)
def _cached(rules_dir: str) -> RuleTables:
    return load_tables(rules_dir)


def get_tables(rules_dir: Path | str | None = None) -> RuleTables:
    """Process-wide cached load. Cache key is the directory path; tests that
    mutate tables on disk must call `load_tables` directly."""
    directory = str(Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR)
    return _cached(directory)
