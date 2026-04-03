"""Deterministic envelope generation from artifact content.

Envelopes are derived programmatically (no LLM) to guarantee correctness —
diff search targets are real substrings, section IDs match actual markers.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .markers import extract_section_content, markers_for


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


# ── Diff targets ────────────────────────────────────────────────────────────


def _extract_diff_targets(content: str, count: int = 8) -> list[str]:
    """Pick non-empty, non-marker lines as diff search targets."""
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
    """Create a deterministic replacement for a diff target."""
    mutated = re.sub(r"\d+", lambda m: str(int(m.group()) + 42), target)
    if mutated != target:
        return mutated
    h = hashlib.md5(target.encode()).hexdigest()[:8]
    return target.replace(target[:5], f"UPD{h}_")


# ── Diff envelopes ──────────────────────────────────────────────────────────


def _diff_replace(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_diff_targets(content, 4)
    return [
        make_envelope(aid, 2 + i, "diff", fmt, [
            {"op": "replace", "target": {"search": t}, "content": _mutate_text(t)},
        ])
        for i, t in enumerate(targets)
    ]


def _diff_delete(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_diff_targets(content, 6)
    return [
        make_envelope(aid, 10 + i, "diff", fmt, [
            {"op": "delete", "target": {"search": t}},
        ])
        for i, t in enumerate(targets[-2:])
    ]


def _diff_multi(content: str, aid: str, fmt: str) -> list[dict]:
    targets = _extract_diff_targets(content, 8)
    if len(targets) < 3:
        return []
    ops = [
        {"op": "replace", "target": {"search": t}, "content": _mutate_text(t)}
        for t in targets[:3]
    ]
    return [make_envelope(aid, 20, "diff", fmt, ops)]


# ── Section envelopes ───────────────────────────────────────────────────────


def _section_single(content: str, aid: str, fmt: str, sids: list[str]) -> list[dict]:
    envs = []
    for i, sid in enumerate(sids):
        sc = extract_section_content(content, sid, fmt)
        if sc is None:
            continue
        lines = sc.strip().split("\n")
        if lines:
            lines[0] = lines[0].upper()
        envs.append(make_envelope(aid, 30 + i, "section", fmt, [
            {"id": sid, "content": "\n".join(lines) + "\n"},
        ]))
    return envs


def _section_multi(content: str, aid: str, fmt: str, sids: list[str]) -> list[dict]:
    valid = [(sid, extract_section_content(content, sid, fmt)) for sid in sids]
    valid = [(sid, sc) for sid, sc in valid if sc is not None]
    if len(valid) < 2:
        return []
    ops = [{"id": sid, "content": sc.strip()[:100] + "\n"} for sid, sc in valid[:3]]
    return [make_envelope(aid, 40, "section", fmt, ops)]


# ── Template envelopes ──────────────────────────────────────────────────────


def _template_fill(content: str, aid: str, fmt: str) -> list[dict]:
    bindings: dict[str, str] = {}
    template = content
    idx = 0

    for m in re.finditer(r'"([^"]{3,25})"', template):
        if idx >= 5:
            break
        val = m.group(1)
        var = f"str_{idx}"
        if f'"{val}"' in template:
            template = template.replace(f'"{val}"', f'"{{{{{var}}}}}"', 1)
            bindings[var] = val
            idx += 1

    for m in re.finditer(r"\b(\d{2,6})\b", template):
        if idx >= 8:
            break
        val = m.group(1)
        var = f"num_{idx}"
        if val in template and f"{{{{{var}}}}}" not in template:
            template = template.replace(val, f"{{{{{var}}}}}", 1)
            bindings[var] = val
            idx += 1

    if not bindings:
        return []
    return [make_envelope(aid, 50, "template", fmt, [
        {"template": template, "bindings": bindings},
    ])]


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


def _diff_pointer(content: str, aid: str, fmt: str) -> list[dict]:
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
        envs.append(make_envelope(aid, 2 + i, "diff", fmt, [
            {"op": "replace", "target": {"pointer": ptr}, "content": new_val},
        ]))
    return envs


# ── Full envelope ───────────────────────────────────────────────────────────


def _full(content: str, aid: str, fmt: str) -> list[dict]:
    return [make_envelope(aid, 1, "full", fmt, [{"body": content}])]


# ── Public API ──────────────────────────────────────────────────────────────


def generate_all_envelopes(
    content: str,
    artifact_id: str,
    fmt: str,
    section_ids: list[str],
) -> dict[str, list[dict]]:
    """Generate all envelope types for an artifact. Returns {filename: [envelopes]}."""
    result: dict[str, list[dict]] = {}

    result["full.jsonl"] = _full(content, artifact_id, fmt)

    if fmt == "application/json":
        envs = _diff_pointer(content, artifact_id, fmt)
        if envs:
            result["diff-pointer.jsonl"] = envs
        envs = _template_fill(content, artifact_id, fmt)
        if envs:
            result["template-fill.jsonl"] = envs
    else:
        envs = _diff_replace(content, artifact_id, fmt)
        if envs:
            result["diff-replace.jsonl"] = envs
        envs = _diff_delete(content, artifact_id, fmt)
        if envs:
            result["diff-delete.jsonl"] = envs
        envs = _diff_multi(content, artifact_id, fmt)
        if envs:
            result["diff-multi.jsonl"] = envs

        valid_sids = [s for s in section_ids if extract_section_content(content, s, fmt) is not None]
        if valid_sids:
            envs = _section_single(content, artifact_id, fmt, valid_sids)
            if envs:
                result["section-single.jsonl"] = envs
            envs = _section_multi(content, artifact_id, fmt, valid_sids)
            if envs:
                result["section-multi.jsonl"] = envs

        envs = _template_fill(content, artifact_id, fmt)
        if envs:
            result["template-fill.jsonl"] = envs

    return result
