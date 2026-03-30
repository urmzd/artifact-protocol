"""
Generation strategy implementations for aap/1.0.

Each function produces an Envelope using the most token-efficient mode
for the given change scenario.
"""
from __future__ import annotations

import difflib
import re

from artifact_generator.aap import (
    Envelope,
    DiffOp,
    Target,
    SectionDef,
    SectionUpdate,
    Include,
    new_id,
    now_iso,
    sha256_checksum,
)


def generate_full(
    content: str,
    format: str = "text/html",
    artifact_id: str | None = None,
    version: int = 1,
    sections: list[SectionDef] | None = None,
) -> Envelope:
    """Generate a full-mode envelope with complete content."""
    return Envelope(
        id=artifact_id or new_id(),
        version=version,
        format=format,
        mode="full",
        content=content,
        created_at=now_iso() if version == 1 else None,
        updated_at=now_iso(),
        checksum=sha256_checksum(content),
        sections=sections or [],
    )


def generate_diff(
    artifact_id: str,
    base_version: int,
    old_content: str,
    new_content: str,
    version: int | None = None,
) -> Envelope:
    """Compute minimal diff operations between old and new content.

    Uses search-based targeting for changed lines — finds the old text
    and replaces with the new text.
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    ops: list[DiffOp] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_text = "".join(old_lines[i1:i2])
        new_text = "".join(new_lines[j1:j2])
        if tag == "replace":
            ops.append(DiffOp(
                op="replace",
                target=Target(search=old_text),
                content=new_text,
            ))
        elif tag == "delete":
            ops.append(DiffOp(
                op="delete",
                target=Target(search=old_text),
            ))
        elif tag == "insert":
            # Insert before the next line in the old content
            if i1 < len(old_lines):
                anchor = old_lines[i1]
                ops.append(DiffOp(
                    op="insert_before",
                    target=Target(search=anchor),
                    content=new_text,
                ))
            else:
                # Appending at end — use offset
                ops.append(DiffOp(
                    op="insert_after",
                    target=Target(offsets=(len(old_content), len(old_content))),
                    content=new_text,
                ))

    return Envelope(
        id=artifact_id,
        version=version or base_version + 1,
        format="text/html",
        mode="diff",
        base_version=base_version,
        updated_at=now_iso(),
        operations=ops,
    )


def generate_section_update(
    artifact_id: str,
    base_version: int,
    updates: dict[str, str],
    version: int | None = None,
) -> Envelope:
    """Generate a section-mode envelope replacing specific sections."""
    return Envelope(
        id=artifact_id,
        version=version or base_version + 1,
        format="text/html",
        mode="section",
        base_version=base_version,
        updated_at=now_iso(),
        target_sections=[
            SectionUpdate(id=sid, content=content)
            for sid, content in updates.items()
        ],
    )


def generate_template_fill(
    template: str,
    bindings: dict[str, str],
    artifact_id: str | None = None,
    version: int = 1,
    format: str = "text/html",
) -> Envelope:
    """Generate a template-mode envelope with slot bindings."""
    return Envelope(
        id=artifact_id or new_id(),
        version=version,
        format=format,
        mode="template",
        updated_at=now_iso(),
        template=template,
        bindings=bindings,
    )


def generate_composite(
    includes: list[Include],
    artifact_id: str | None = None,
    version: int = 1,
    format: str = "text/html",
) -> Envelope:
    """Generate a composite-mode envelope assembling sub-artifacts."""
    return Envelope(
        id=artifact_id or new_id(),
        version=version,
        format=format,
        mode="composite",
        created_at=now_iso(),
        includes=includes,
    )


def extract_sections(html: str) -> list[SectionDef]:
    """Extract section definitions from HTML section markers."""
    pattern = r"<!-- section:(\S+) -->"
    sections = []
    for match in re.finditer(pattern, html):
        sid = match.group(1)
        sections.append(SectionDef(
            id=sid,
            start_marker=f"<!-- section:{sid} -->",
            end_marker=f"<!-- /section:{sid} -->",
        ))
    return sections


def get_section_content(html: str, section_id: str) -> str:
    """Extract the content between section markers."""
    start_marker = f"<!-- section:{section_id} -->"
    end_marker = f"<!-- /section:{section_id} -->"
    si = html.find(start_marker)
    ei = html.find(end_marker)
    if si == -1 or ei == -1:
        raise ValueError(f"Section not found: {section_id}")
    return html[si + len(start_marker) : ei].strip()
