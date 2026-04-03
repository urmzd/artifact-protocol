"""Deterministic envelope generation from artifact content.

Envelopes are derived programmatically (no LLM) to guarantee correctness —
edit search targets are real substrings, section IDs match actual markers.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .markers import markers_for


def make_envelope(
    artifact_id: str, version: int, name: str, fmt: str, content: list[Any],
) -> dict:
    return {
        "protocol": "aap/0.1",
        "id": artifact_id,
        "version": version,
        "name": name,
        "operation": {"direction": "output", "format": fmt},
        "content": content,
    }


# ── Edit targets ───────────────────────────────────────────────────────────


def _extract_edit_targets(content: str, count: int = 8) -> list[str]:
    """Pick non-empty, non-marker lines as edit search targets."""
    candidates = []
    for line in content.split("\n"):
        stripped = line.strip()
        if len(stripped) < 10 or len(stripped) > 200:
            continue
        if "section:" in stripped or "#region" in stripped or "#endregion" in stripped:
            continue
        if "region " in stripped and stripped.startswith("#"):
            continue
        if stripped in ("{", "}", "[", "]", "(", ")", "};", "],"):
            continue
        candidates.append(line.rstrip("\n"))

    if not candidates:
        return []
    step = max(1, len(candidates) // count)
    return [candidates[i] for i in range(0, len(candidates), step)][:count]


def _mutate_text(target: str) -> str:
    """Create a deterministic replacement for an edit target."""
    mutated = re.sub(r"\d+", lambda m: str(int(m.group()) + 42), target)
    if mutated != target:
        return mutated
    h = hashlib.md5(target.encode()).hexdigest()[:8]
    return target.replace(target[:5], f"UPD{h}_")


# ── Edit envelopes (id-based targeting) ────────────────────────────────────


def _edit_replace(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_edit_targets(content, 4)
    return [
        make_envelope(aid, 2 + i, "edit", fmt, [
            {"op": "replace", "target": {"type": "id", "value": t}, "content": _mutate_text(t)},
        ])
        for i, t in enumerate(targets)
    ]


def _edit_delete(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_edit_targets(content, 6)
    return [
        make_envelope(aid, 10 + i, "edit", fmt, [
            {"op": "delete", "target": {"type": "id", "value": t}},
        ])
        for i, t in enumerate(targets[-2:])
    ]


def _edit_multi(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_edit_targets(content, 8)
    if len(targets) < 3:
        return []
    ops = [
        {"op": "replace", "target": {"type": "id", "value": t}, "content": _mutate_text(t)}
        for t in targets[:3]
    ]
    return [make_envelope(aid, 20, "edit", fmt, ops)]


# ── JSON pointer envelopes ─────────────────────────────────────────────────


def _extract_pointers(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    results = []
    if isinstance(value, dict):
        for k, v in value.items():
            escaped = k.replace("~", "~0").replace("/", "~1")
            path = f"{prefix}/{escaped}"
            results.append((path, v))
            results.extend(_extract_pointers(v, path))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            path = f"{prefix}/{i}"
            results.append((path, v))
            results.extend(_extract_pointers(v, path))
    return results


def _edit_pointer(content: str, aid: str, fmt: str) -> list[dict]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []

    leaves = [(p, v) for p, v in _extract_pointers(parsed) if not isinstance(v, (dict, list))]
    if not leaves:
        return []

    envs = []
    for i, (ptr, val) in enumerate(leaves[:4]):
        if isinstance(val, str):
            new_val = json.dumps(val + "_updated")
        elif isinstance(val, (int, float)):
            new_val = json.dumps(val + 42)
        elif isinstance(val, bool):
            new_val = json.dumps(not val)
        else:
            new_val = json.dumps("null_replaced")
        envs.append(make_envelope(aid, 2 + i, "edit", fmt, [
            {"op": "replace", "target": {"type": "pointer", "value": ptr}, "content": new_val},
        ]))
    return envs


# ── Synthesize envelope ────────────────────────────────────────────────────


def _synthesize(content: str, aid: str, fmt: str) -> list[dict]:
    return [make_envelope(aid, 1, "synthesize", fmt, [{"body": content}])]


# ── Public API ──────────────────────────────────────────────────────────────


def generate_all_envelopes(
    content: str,
    artifact_id: str,
    fmt: str,
    section_ids: list[str],
) -> dict[str, list[dict]]:
    """Generate all envelope types for an artifact. Returns {filename: [envelopes]}."""
    result: dict[str, list[dict]] = {}

    result["synthesize.jsonl"] = _synthesize(content, artifact_id, fmt)

    if fmt == "application/json":
        envs = _edit_pointer(content, artifact_id, fmt)
        if envs:
            result["edit-pointer.jsonl"] = envs
    else:
        envs = _edit_replace(content, artifact_id, fmt)
        if envs:
            result["edit-replace.jsonl"] = envs
        envs = _edit_delete(content, artifact_id, fmt)
        if envs:
            result["edit-delete.jsonl"] = envs
        envs = _edit_multi(content, artifact_id, fmt)
        if envs:
            result["edit-multi.jsonl"] = envs

    return result
