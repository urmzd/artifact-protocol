"""AAP envelope application — resolves diff and section operations.

Tries the Rust engine via PyO3 FFI first, falls back to pure Python.
"""

from __future__ import annotations

import re

from .markers import markers_for

# Try Rust FFI, fall back to pure Python
try:
    from aap_evals._engine import resolve as _rust_resolve  # type: ignore[import-not-found]
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False


def apply_envelope(content: str, name: str, items: list[dict], fmt: str) -> str:
    """Resolve an AAP envelope against artifact content."""
    if name == "diff":
        return _apply_diff(content, items)
    elif name == "section":
        return _apply_section_update(content, items, fmt)
    else:
        raise ValueError(f"unsupported operation name: {name}")


def _apply_diff(content: str, items: list[dict]) -> str:
    result = content
    for item in items:
        op = item.get("op", "")
        search = item.get("target", {}).get("search", "")
        replacement = item.get("content", "")

        if not search:
            raise ValueError("diff op missing search target")
        if search not in result:
            raise ValueError(f"search target not found: {search[:80]!r}")

        if op == "replace":
            result = result.replace(search, replacement, 1)
        elif op == "delete":
            result = result.replace(search, "", 1)
        elif op == "insert_before":
            idx = result.index(search)
            result = result[:idx] + replacement + result[idx:]
        elif op == "insert_after":
            idx = result.index(search) + len(search)
            result = result[:idx] + replacement + result[idx:]
        else:
            raise ValueError(f"unknown diff op: {op}")
    return result


def _apply_section_update(content: str, items: list[dict], fmt: str) -> str:
    result = content
    for item in items:
        section_id = item.get("id", "")
        new_content = item.get("content", "")
        pair = markers_for(section_id, fmt)
        if not pair:
            raise ValueError(f"no markers for format {fmt!r}")
        start, end = pair

        pattern = re.escape(start) + r"[\s\S]*?" + re.escape(end)
        replacement = f"{start}\n{new_content}\n{end}"
        new_result = re.sub(pattern, replacement, result, count=1)

        if new_result == result:
            raise ValueError(f"section {section_id!r} not found in content")
        result = new_result
    return result
