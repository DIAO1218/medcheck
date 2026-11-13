"""Live extractor: an OpenAI-compatible chat endpoint over stdlib urllib.

Two rules shape this module:
  * the model sees only masked text (privacy.mask runs before this);
  * the model's payload passes `guard.check_payload` before it becomes an
    `ExtractionRecord`, so a model-supplied verdict aborts the case (INV-003).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ..contracts import ExtractionRecord
from .context import assemble

VERSION = "llm-v1.0"


class MissingModelError(RuntimeError):
    """No endpoint/key configured: the caller must hold the case (P-01)."""


def configured() -> bool:
    return bool(os.environ.get("MEDCHECK_LLM_BASE_URL") and os.environ.get("MEDCHECK_LLM_API_KEY"))


def extract(
    masked_note: str,
    vocabulary: tuple[str, ...] | list[str] = (),
    *,
    timeout: float = 8.0,
) -> ExtractionRecord:
    if not configured():
        raise MissingModelError(
            "MEDCHECK_LLM_BASE_URL / MEDCHECK_LLM_API_KEY are not set; "
            "the case must be held (P-01) rather than guessed"
        )

    context = assemble(masked_note, vocabulary)
    endpoint = os.environ["MEDCHECK_LLM_BASE_URL"].rstrip("/") + "/chat/completions"
    body = {
        "model": os.environ.get("MEDCHECK_LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": context.payload}],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['MEDCHECK_LLM_API_KEY']}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))

    content = payload["choices"][0]["message"].get("content") or ""
    parsed: dict[str, Any] = json.loads(_last_json_object(content))

    # The contract refuses authority fields itself; the extractor does not need
    # (and must not import) the adjudicator's guard.
    return ExtractionRecord.from_payload(parsed, prompt_version=VERSION)


def _last_json_object(text: str) -> str:
    """The gateway used in this course puts the answer (and its reasoning) in one
    string, often with prose around it. Take the last balanced JSON object."""
    depth = 0
    start = -1
    candidate = ""
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                candidate = text[start : index + 1]
    if not candidate:
        raise ValueError("no JSON object found in model response")
    return candidate


def extract_with_fallback(
    masked_note: str,
    vocabulary: tuple[str, ...] | list[str] = (),
    *,
    allow_heuristic: bool | None = None,
) -> ExtractionRecord:
    """Live extractor with an explicit, opt-in offline fallback (P-01).

    The fallback is never silent: `MEDCHECK_ALLOW_HEURISTIC` must be set, which is
    only acceptable in dev/CI. Production holds instead.
    """
    from . import heuristic

    allow = (
        os.environ.get("MEDCHECK_ALLOW_HEURISTIC") == "1"
        if allow_heuristic is None
        else allow_heuristic
    )
    try:
        return extract(masked_note, vocabulary)
    except (MissingModelError, urllib.error.URLError, TimeoutError, ValueError, KeyError):
        if not allow:
            raise
        record = heuristic.extract(masked_note, vocabulary)
        return ExtractionRecord(
            medications=record.medications,
            egfr=record.egfr,
            unparsed=record.unparsed + ("extractor: heuristic fallback",),
            prompt_version=heuristic.VERSION,
        )
