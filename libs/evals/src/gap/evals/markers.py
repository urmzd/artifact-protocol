"""Universal XML target markers — mirrors src/markers.rs.

All formats use `<gap:target id="...">` / `</gap:target>`.
JSON uses pointer addressing instead.
"""

from __future__ import annotations


def markers_for(target_id: str, fmt: str) -> tuple[str, str] | None:
    """Return (start, end) marker pair, or None for JSON."""
    if fmt == "application/json":
        return None
    return f'<gap:target id="{target_id}">', "</gap:target>"


def marker_example(fmt: str) -> str:
    """Return a human-readable marker example for prompts."""
    if fmt == "application/json":
        return ""
    return '<gap:target id="ID"> ... </gap:target>'


def _find_matching_close(content: str, content_start: int) -> int:
    """Find the position of the matching </gap:target> with depth counting."""
    open_prefix = "<gap:target "
    close_tag = "</gap:target>"
    depth = 1
    cursor = content_start

    while cursor < len(content) and depth > 0:
        next_open = content.find(open_prefix, cursor)
        next_close = content.find(close_tag, cursor)

        if next_close == -1:
            return -1

        if next_open != -1 and next_open < next_close:
            depth += 1
            cursor = next_open + len(open_prefix)
        else:
            depth -= 1
            if depth == 0:
                return next_close
            cursor = next_close + len(close_tag)

    return -1


def extract_target_content(content: str, target_id: str, fmt: str) -> str | None:
    pair = markers_for(target_id, fmt)
    if not pair:
        return None
    start, end = pair
    si = content.find(start)
    if si == -1:
        return None
    content_start = si + len(start)
    ei = _find_matching_close(content, content_start)
    if ei == -1:
        return None
    return content[content_start:ei]
