"""Spec-compliant AAP Pydantic models — mirrors ../src/aap.rs.

Four envelope types: synthesize (full generation), edit (targeted changes),
handle (lightweight reference), handle_result (response from handle interaction).
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ── Target definitions ────────────────────────────────────────────────────


class TargetDef(BaseModel):
    """Named target in an artifact."""

    id: str
    label: str | None = None


class IdTarget(BaseModel):
    """Target an <aap:target id="..."> marker by ID."""

    type: Literal["id"]
    value: str


class PointerTarget(BaseModel):
    """Target a value by JSON Pointer (RFC 6901)."""

    type: Literal["pointer"]
    value: str


DiffTarget = Annotated[
    Union[IdTarget, PointerTarget],
    Field(discriminator="type"),
]


class DiffOp(BaseModel):
    """A single edit operation."""

    op: Literal["replace", "insert_before", "insert_after", "delete"]
    target: DiffTarget
    content: str | None = None


class SynthesizeContentItem(BaseModel):
    """Content item for name=synthesize."""

    body: str
    targets: list[TargetDef] | None = None


# ── Operation metadata ────────────────────────────────────────────────────


class OperationMeta(BaseModel):
    """Envelope operation metadata."""

    direction: Literal["input", "output"] = "output"
    format: str = "text/html"
    tokens_used: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ── Typed envelope variants ───────────────────────────────────────────────


class SynthesizeEnvelope(BaseModel):
    """Envelope for name=synthesize (full artifact generation)."""

    protocol: Literal["aap/0.1"] = "aap/0.1"
    id: str
    version: int
    name: Literal["synthesize"]
    operation: OperationMeta = Field(default_factory=OperationMeta)
    content: list[SynthesizeContentItem]


class EditEnvelope(BaseModel):
    """Envelope for name=edit (targeted changes via id/pointer targeting)."""

    protocol: Literal["aap/0.1"] = "aap/0.1"
    id: str
    version: int
    name: Literal["edit"]
    operation: OperationMeta = Field(default_factory=OperationMeta)
    content: list[DiffOp]


# ── Handle types ──────────────────────────────────────────────────────────


class HandleContentItem(BaseModel):
    """Content item for name=handle."""

    sections: list[str]
    token_count: int | None = None
    state: str | None = None


class HandleEnvelope(BaseModel):
    """Envelope for name=handle (lightweight artifact reference)."""

    protocol: Literal["aap/0.1"] = "aap/0.1"
    id: str
    version: int
    name: Literal["handle"]
    operation: OperationMeta = Field(default_factory=OperationMeta)
    content: list[HandleContentItem]


# ── Handle result types ───────────────────────────────────────────────────


class TextResult(BaseModel):
    """Free-form text response from handle interaction."""

    type: Literal["text"]
    body: str


class EditResult(BaseModel):
    """Edit confirmation from handle interaction."""

    type: Literal["edit"]
    status: str
    changes: list[dict] = Field(default_factory=list)


class ErrorResult(BaseModel):
    """Error response from handle interaction."""

    type: Literal["error"]
    code: str
    message: str


HandleResultContentItem = Annotated[
    Union[TextResult, EditResult, ErrorResult],
    Field(discriminator="type"),
]


class HandleResultEnvelope(BaseModel):
    """Envelope for name=handle_result (response from handle interaction)."""

    protocol: Literal["aap/0.1"] = "aap/0.1"
    id: str
    version: int
    name: Literal["handle_result"]
    operation: OperationMeta = Field(default_factory=OperationMeta)
    content: list[HandleResultContentItem]


# ── Envelope union ────────────────────────────────────────────────────────


Envelope = Annotated[
    Union[SynthesizeEnvelope, EditEnvelope, HandleEnvelope, HandleResultEnvelope],
    Field(discriminator="name"),
]
