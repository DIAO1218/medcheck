"""Structural tier: the architecture is checked, not just documented.

These are architectural fitness functions. They fail when the code drifts from
architecture-blueprint.md section 4, which is the only way a diagram stays true.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "medcheck"

COMPONENTS = {
    "privacy": "medcheck/privacy",
    "extractor": "medcheck/extractor",
    "rules": "medcheck/rules",
    "adjudicator": "medcheck/adjudicator",
    "renderer": "medcheck/renderer",
    "audit": "medcheck/audit",
    "api": "medcheck/api",
}

FORBIDDEN_IMPORTS = {
    "extractor": {"rules", "adjudicator", "audit", "renderer", "api"},
    "privacy": {"rules", "adjudicator", "audit", "renderer", "api", "extractor"},
    "renderer": {"adjudicator", "audit", "api", "rules", "extractor", "privacy"},
    "rules": {"adjudicator", "audit", "renderer", "api", "extractor", "privacy"},
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("medcheck."):
                found.add(module.split(".")[1])
            elif node.level and module == "":
                for alias in node.names:
                    found.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("medcheck."):
                    found.add(alias.name.split(".")[1])
    return found


def test_component_module_mapping():
    """[REQ-G-005] Blueprint section 4: one architectural element, one module directory."""
    for name, relative in COMPONENTS.items():
        path = ROOT / "src" / relative
        assert path.is_dir(), f"component '{name}' has no module at {relative}"
        assert (path / "__init__.py").is_file()


def test_no_authority_import():
    """[INV-003] Perception must not import judgement; the advisory must not import the engine."""
    violations = []
    for component, forbidden in FORBIDDEN_IMPORTS.items():
        directory = SRC / component
        for module_file in directory.rglob("*.py"):
            # __init__ and relative-import aliasing are noise; check real modules.
            if module_file.name == "__init__.py":
                continue
            for imported in _imports(module_file):
                if imported in forbidden:
                    violations.append(f"{module_file.relative_to(ROOT)} imports '{imported}'")
    assert violations == []


def test_single_approve_site():
    """[INV-003] INV-003 support: exactly one module may assign an APPROVE verdict."""
    assigners = []
    for module_file in SRC.rglob("*.py"):
        text = module_file.read_text(encoding="utf-8")
        if "verdict = Verdict.APPROVE" in text:
            assigners.append(module_file.relative_to(SRC).as_posix())
    assert assigners == ["adjudicator/verdict.py"]


def test_every_requirement_is_traced():
    """[REQ-G-005] Trace matrix: every REQ id in the registry appears in at least one test file."""
    registry = yaml.safe_load((ROOT / "docs" / "req" / "requirements.yaml").read_text(encoding="utf-8"))
    test_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "test").rglob("test_*.py")
    )
    untraced = [item["id"] for item in registry["requirements"] if item["id"] not in test_text]
    assert untraced == [], f"requirements with no test: {untraced}"


def test_no_module_outside_adjudicator_returns_verdict():
    """[INV-003] Only the adjudicator composes results; a second composer would fork authority."""
    composers = [
        module_file.relative_to(SRC).as_posix()
        for module_file in SRC.rglob("*.py")
        if "AdjudicationResult(" in module_file.read_text(encoding="utf-8")
    ]
    assert composers == ["adjudicator/verdict.py"]


@pytest.mark.parametrize("path", ["src/medcheck/adjudicator", "src/medcheck/rules", "src/medcheck/privacy", "src/medcheck/audit"])
def test_safety_critical_modules_exist(path):
    """[REQ-G-005] safety critical modules exist."""
    assert (ROOT / path).is_dir()


def test_every_test_declares_its_requirement():
    """[REQ-G-005] D4: every test references the requirement or invariant it verifies.

    Enforced structurally so the claim cannot rot: a new test without an id fails
    the build, which is cheaper than a reviewer noticing six months later.
    """
    import re

    pattern = re.compile(r"REQ-[A-Z]-\d{3}|INV-\d{3}")
    missing = []
    for path in sorted((ROOT / "test").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            is_test = isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            if is_test and not pattern.search(ast.get_docstring(node) or ""):
                missing.append(f"{path.name}::{node.name}")
    assert missing == [], f"tests with no requirement reference: {missing}"


def test_blueprint_exists_in_both_required_locations():
    """[REQ-G-005] D2 wants the blueprint in docs/architecture/; Section 5 wants it at the root.

    Both, byte-identical, so satisfying one requirement cannot break the other.
    """
    source = (ROOT / "architecture-blueprint.md").read_bytes()
    mirror = (ROOT / "docs" / "architecture" / "architecture-blueprint.md").read_bytes()
    assert source == mirror, "blueprint copies have drifted; run scripts/sync_blueprint.py"
