"""GAP envelope application — delegates to Rust apply engine via PyO3 FFI."""

from __future__ import annotations

import json

from .schema import EditEnvelope, SynthesizeEnvelope, LLMEnvelope

try:
    from gap.core import resolve_envelope as _rust_resolve  # type: ignore[import-not-found]
except ImportError as exc:
    raise ImportError(
        "Rust apply engine not available — run `just bind`"
    ) from exc


type AnyEnvelope = LLMEnvelope


def apply_envelope(artifact: str, envelope: AnyEnvelope, fmt: str) -> str:
    """Resolve a typed GAP envelope against artifact content via Rust FFI.

    Returns the resolved artifact body string.
    """
    operation_json = envelope.model_dump_json(exclude_none=True)

    # FFI expects Artifact JSON (not an envelope) as base
    artifact_json = json.dumps({
        "id": envelope.id,
        "version": envelope.version - 1,
        "format": fmt,
        "body": artifact,
    })

    if isinstance(envelope, SynthesizeEnvelope):
        result_json = _rust_resolve(operation_json, None)
    else:
        result_json = _rust_resolve(operation_json, artifact_json)

    result = json.loads(result_json)
    return result["artifact"]["body"]
