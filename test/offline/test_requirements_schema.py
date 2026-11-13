"""Schema gate self-test (CI gate 3).

The gate must fail on a registry that violates the schema, and must fail the
cross-field rules a JSON Schema cannot express. A gate that cannot fail is
decoration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_requirements.py"
REGISTRY = ROOT / "docs" / "req" / "requirements.yaml"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, timeout=60
    )


def test_registry_validates():
    """[REQ-G-005] registry validates."""
    result = _run()
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


def test_registry_rejects_broken_invariant(tmp_path):
    """[REQ-G-005] An invariant without zero_tolerance must be refused."""
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    for item in registry["requirements"]:
        if item["type"] == "invariant":
            item.pop("zero_tolerance", None)
            break
    broken = tmp_path / "requirements.yaml"
    broken.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    result = _run("--registry", str(broken))
    assert result.returncode == 1
    assert "zero_tolerance" in result.stderr


def test_registry_rejects_unfalsifiable_criterion(tmp_path):
    """[REQ-G-005] A fit criterion without a quantity is not machine-checkable."""
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    for item in registry["requirements"]:
        if item["type"] == "invariant":
            item["fit_criterion"] = "the system must behave safely in all cases at all times"
            break
    broken = tmp_path / "requirements.yaml"
    broken.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    result = _run("--registry", str(broken))
    assert result.returncode == 1
    assert "falsifiable" in result.stderr


def test_registry_rejects_undeclared_source(tmp_path):
    """[REQ-G-005] registry rejects undeclared source."""
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    registry["requirements"][0]["source"] = "SRC-NOT-DECLARED"
    broken = tmp_path / "requirements.yaml"
    broken.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    result = _run("--registry", str(broken))
    assert result.returncode == 1
    assert "not declared" in result.stderr


def test_registry_has_the_five_invariants():
    """[REQ-G-005] registry has the five invariants."""
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    invariants = [item for item in registry["requirements"] if item["type"] == "invariant"]
    assert len(invariants) == 5
    assert all(item["zero_tolerance"] is True for item in invariants)
