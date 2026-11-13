"""REQ-S-001 / REQ-S-002 — repository hygiene gates."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "medcheck"

#: Direct third-party imports allowed by REQ-S-002. Everything else must be
#: standard library, and the list is short on purpose.
ALLOWLIST = {"yaml", "jsonschema", "pytest"}


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_all_imports_allowlisted():
    """REQ-S-002: no dependency enters src/ without an allowlist decision."""
    outside = set()
    for module_file in SRC.rglob("*.py"):
        for name in _top_level_imports(module_file):
            if name in {"medcheck"} or name in sys.stdlib_module_names or name in ALLOWLIST:
                continue
            outside.add(f"{module_file.relative_to(ROOT)}: {name}")
    assert outside == set(), f"dependencies outside the allowlist: {sorted(outside)}"


def test_no_real_identifiers_in_fixtures():
    """[REQ-S-001] REQ-S-001: committed fixtures are synthetic; no PHI, no secrets."""
    import re

    patterns = {
        "hkid": re.compile(r"\b[A-Z]{1,2}\d{6}\(\d|A\)"),
        "phone": re.compile(r"\b(?:\+852[\s-]?)?[2-9]\d{3}[\s-]?\d{4}\b"),
        "email": re.compile(r"\b[\w.]+@[\w.]+\.[a-z]{2,}\b"),
        "key": re.compile(r"\b(sk-[A-Za-z0-9]{10,}|api[_-]?key\s*[:=])", re.IGNORECASE),
    }
    hits = []
    for path in (ROOT / "test" / "fixtures").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in patterns.items():
                if pattern.search(text):
                    hits.append(f"{path.name}: {label}")
    assert hits == [], f"possible PHI or secret in fixtures: {hits}"


def test_model_endpoint_is_not_hardcoded():
    """[REQ-S-002] REQ-S-002: the endpoint is configuration, never a literal in code."""
    text = (SRC / "extractor" / "llm.py").read_text(encoding="utf-8")
    assert "https://" not in text
    assert "MEDCHECK_LLM_BASE_URL" in text


def test_no_repository_file_contains_a_key():
    """[REQ-S-001] A blunt check that still catches the common mistake."""
    suspicious = []
    for path in ROOT.rglob("*.py"):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "sk-" + "proj" in text or "Bearer " + "ey" in text:
            suspicious.append(path.name)
    assert suspicious == []
