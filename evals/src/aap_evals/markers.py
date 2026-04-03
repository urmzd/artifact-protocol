"""Universal XML target markers — mirrors src/markers.rs.

All formats use `<aap:target id="...">` / `</aap:target>`.
JSON uses pointer addressing instead.
"""

from __future__ import annotations


def markers_for(target_id: str, fmt: str) -> tuple[str, str] | None:
    """Return (start, end) marker pair, or None for JSON."""
    if fmt == "application/json":
        return None
    return f'<aap:target id="{target_id}">', "</aap:target>"


def marker_example(fmt: str) -> str:
    """Return a human-readable marker example for prompts."""
    if fmt == "application/json":
        return ""
    return '<aap:target id="ID"> ... </aap:target>'


def extract_target_content(content: str, target_id: str, fmt: str) -> str | None:
    pair = markers_for(target_id, fmt)
    if not pair:
        return None
    start, end = pair
    si = content.find(start)
    ei = content.find(end)
    if si == -1 or ei == -1:
        return None
    return content[si + len(start) : ei]
