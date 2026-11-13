"""Permission evaluation: deny by default, allow only by explicit pattern.

This module is the code that `permissions.jsonc` describes. The test suite checks
that the two agree (REQ-G-002): 12 unlisted requests across 3 roles, 12 denials.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parents[3] / ".opencode" / "permissions.jsonc"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def load_policy(path: Path | str | None = None) -> dict[str, Any]:
    target = Path(path) if path else DEFAULT_PATH
    raw = target.read_text(encoding="utf-8")
    return json.loads(_strip_jsonc(raw))


def _strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments and trailing commas; JSONC stays readable."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"(?<!:)//[^\n]*", "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text


def _normalise(path: str) -> str:
    """Forward slashes, no leading './' or '/'.

    Deliberately not `lstrip('./')`: that would strip the dot of '.env' and the
    leading dot of '.opencode/', turning a deny rule into a no-op.
    """
    normalised = path.replace("\\", "/")
    while normalised.startswith("./"):
        normalised = normalised[2:]
    return normalised.lstrip("/")


def _matches(path: str, patterns: list[str]) -> bool:
    normalised = _normalise(path)
    for pattern in patterns:
        if fnmatch.fnmatch(normalised, _normalise(pattern).replace("**", "*")):
            return True
    return False


def check(path: str, role: str, mode: str = "read", policy: dict[str, Any] | None = None) -> Decision:
    policy = policy or load_policy()
    normalised = _normalise(path)

    if role not in policy["roles"]:
        return Decision(False, f"unknown role '{role}'; default deny")

    role_rule = policy["roles"][role]

    # 1. data stores and secrets are unreadable to every role (INV-004)
    if mode == "read" and _matches(normalised, policy.get("global_deny_read", [])):
        return Decision(False, "path is a protected data store or secret")

    # 2. human-only surfaces: readable, never writable by an agent
    if mode == "write" and _matches(normalised, policy.get("human_only_write", [])):
        return Decision(False, f"'{normalised}' is human-only; agents may propose, humans commit")

    # 3. explicit deny beats any allow
    if mode == "write" and _matches(normalised, role_rule.get("deny_write", [])):
        return Decision(False, f"'{normalised}' is explicitly denied for {role}")

    # 4. allow only by whitelist
    if _matches(normalised, role_rule.get(mode, [])):
        return Decision(True, f"granted by {role}.{mode}")

    return Decision(False, f"'{normalised}' is not whitelisted for {role}.{mode}")


def allowed(path: str, role: str, mode: str = "read", policy: dict[str, Any] | None = None) -> bool:
    return check(path, role, mode, policy).allowed


def shell_allowed(command: str, policy: dict[str, Any] | None = None) -> bool:
    policy = policy or load_policy()
    return any(command.strip().startswith(prefix) for prefix in policy.get("shell_allowlist", []))


def safety_critical(path: str, policy: dict[str, Any] | None = None) -> bool:
    policy = policy or load_policy()
    return _matches(path, policy["guards"]["safety_critical_paths"])
