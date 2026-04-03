"""Spec-compliant AAP Pydantic models — matches spec/aap.md."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DiffTarget(BaseModel):
    """Addressing mode for diff operations. Exactly one field should be set."""

    search: str | None = None
    section: str | None = None
    lines: list[int] | None = None
    offsets: list[int] | None = None
    pointer: str | None = None


class DiffOp(BaseModel):
    """A single diff operation."""

    op: Literal["replace", "insert_before", "insert_after", "delete"]
    target: DiffTarget
    content: str | None = None


class SectionUpdate(BaseModel):
    """Replace a named section's content."""

    id: str
    content: str


class SectionDef(BaseModel):
    """Section definition within a full envelope."""

    id: str
    label: str | None = None
    start_marker: str | None = None
    end_marker: str | None = None


class FullContentItem(BaseModel):
    """Content item for name=full."""

    body: str
    sections: list[SectionDef] | None = None


class TemplateContentItem(BaseModel):
    """Content item for name=template."""

    template: str
    bindings: dict[str, str]


class OperationMeta(BaseModel):
    """Envelope operation metadata."""

    direction: Literal["input", "output"] = "output"
    format: str = "text/html"
    tokens_used: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Envelope(BaseModel):
    """Spec-compliant AAP envelope — structured output from the maintain context."""

    protocol: Literal["aap/0.1"] = "aap/0.1"
    id: str
    version: int
    name: Literal["full", "diff", "section", "template"]
    operation: OperationMeta = Field(default_factory=OperationMeta)
    content: list[dict[str, Any]]
