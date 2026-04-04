//! PyO3 bindings for the GAP apply engine.
//!
//! Exposes `resolve_envelope` to Python. Takes an operation envelope JSON
//! and an optional base artifact JSON, returns `{"artifact": {...}, "handle": {...}}`.

use pyo3::prelude::*;

use crate::gap::{Artifact, Envelope};
use crate::apply;

/// Resolve a GAP operation against an optional base artifact.
///
/// Args:
///     operation_json: JSON string of the operation envelope (synthesize or edit).
///     artifact_json: JSON string of the base artifact. Required for edit ops.
///
/// Returns:
///     JSON string: `{"artifact": {...}, "handle": {...}}`
#[pyfunction]
fn resolve_envelope(operation_json: &str, artifact_json: Option<&str>) -> PyResult<String> {
    let operation: Envelope = serde_json::from_str(operation_json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("invalid envelope JSON: {e}")))?;

    let artifact = artifact_json
        .map(|json| {
            serde_json::from_str::<Artifact>(json)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("invalid artifact JSON: {e}")))
        })
        .transpose()?;

    let (result_artifact, handle) = apply::apply(artifact.as_ref(), &operation)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("apply failed: {e}")))?;

    let output = serde_json::json!({
        "artifact": result_artifact,
        "handle": handle,
    });

    serde_json::to_string(&output)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("serialization failed: {e}")))
}

/// GAP apply engine Python module.
#[pymodule(name = "_gap")]
fn gap_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(resolve_envelope, m)?)?;
    Ok(())
}
