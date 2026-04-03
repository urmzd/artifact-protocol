"""AAP envelope application — delegates to Rust apply engine via PyO3 FFI."""

from __future__ import annotations

import json

from .schema import DiffEnvelope, FullEnvelope

try:
    from aap_evals.aap import resolve_envelope as _rust_resolve  # type: ignore[import-not-found]
except ImportError as exc:
    raise ImportError(
        "Rust apply engine not available — run `just bind`"
    ) from exc


type AnyEnvelope = FullEnvelope | DiffEnvelope


def apply_envelope(artifact: str, envelope: AnyEnvelope, fmt: str) -> str:
    """Resolve a typed AAP envelope against artifact content via Rust FFI."""
    operation_json = envelope.model_dump_json(exclude_none=True)

    artifact_envelope = json.dumps({
        "protocol": "aap/0.1",
        "id": envelope.id,
        "version": envelope.version - 1,
        "name": "full",
        "operation": {"direction": "output", "format": fmt},
        "content": [{"body": artifact}],
    })

    if isinstance(envelope, FullEnvelope):
        result_json = _rust_resolve(operation_json, None)
    else:
        result_json = _rust_resolve(operation_json, artifact_envelope)

    result = json.loads(result_json)
    return result["content"][0]["body"]
