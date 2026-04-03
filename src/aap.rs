//! Agent-Artifact Protocol (AAP) data model — Rust implementation of aap/0.1.
//!
//! Provides serde-compatible types for envelopes, diff operations, section
//! updates, template bindings, chunk frames, and token budgets.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const PROTOCOL_VERSION: &str = "aap/0.1";

/// Artifact lifecycle state.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ArtifactState {
    Draft,
    Published,
    Archived,
}

/// Operation name — discriminator for envelope content shape.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Name {
    Full,
    Diff,
    Section,
    Template,
    Composite,
    Manifest,
    Handle,
    Projection,
    Intent,
    Result,
    Audit,
}

/// Token budget constraints.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenBudget {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub priority: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_sections: Option<u64>,
}

/// Operation metadata object (Section 3.1.1 of spec).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Operation {
    pub direction: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_encoding: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_id: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_budget: Option<TokenBudget>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub checksum: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_at: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated_at: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<ArtifactState>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state_changed_at: Option<String>,
}

/// Top-level envelope wrapping all protocol payloads.
///
/// The `content` field is always an array of objects whose shape
/// depends on `name`. We store it as raw JSON values and parse
/// per-name in the resolve engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    pub protocol: String,
    pub id: String,
    pub version: u64,
    pub name: Name,
    pub operation: Operation,
    pub content: Vec<serde_json::Value>,
}

impl Envelope {
    /// Check whether this JSON string looks like a protocol envelope.
    pub fn is_envelope(s: &str) -> bool {
        let trimmed = s.trim_start();
        trimmed.starts_with('{') && trimmed.contains("\"aap/")
    }

    /// Parse from JSON string.
    pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(s)
    }
}

/// Section definition within an artifact.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionDef {
    pub id: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub start_marker: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub end_marker: Option<String>,
}

/// Content item for `name: "full"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FullContentItem {
    pub body: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub sections: Option<Vec<SectionDef>>,
}

/// A single diff operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiffOp {
    pub op: OpType,
    pub target: Target,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
}

/// Diff operation type.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum OpType {
    Replace,
    InsertBefore,
    InsertAfter,
    Delete,
}

/// Target addressing for diff operations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Target {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub section: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub lines: Option<[u64; 2]>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub offsets: Option<[u64; 2]>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub search: Option<String>,

    /// JSON Pointer path (RFC 6901) for targeting values in JSON/YAML content.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pointer: Option<String>,
}

/// Section content replacement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionUpdate {
    pub id: String,
    pub content: String,
}

/// Content item for `name: "template"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateContentItem {
    pub template: String,
    pub bindings: HashMap<String, serde_json::Value>,
}

/// Include reference for composite mode.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Include {
    #[serde(rename = "ref", skip_serializing_if = "Option::is_none")]
    pub reference: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub uri: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub hash: Option<String>,
}

/// Content item for `name: "manifest"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestContentItem {
    pub skeleton: String,
    pub section_prompts: Vec<SectionPromptDef>,
}

/// Per-section generation instruction in a manifest.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionPromptDef {
    pub id: String,
    pub prompt: String,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub dependencies: Vec<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_budget: Option<u64>,
}

/// SSE error event payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SseError {
    pub code: String,
    pub message: String,
    #[serde(default, skip_serializing_if = "is_false")]
    pub fatal: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub seq: Option<u64>,
}

/// Streaming chunk frame.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkFrame {
    pub seq: u64,
    pub content: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub envelope: Option<serde_json::Value>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_id: Option<String>,

    #[serde(default, skip_serializing_if = "is_false")]
    pub flush: bool,

    #[serde(default, rename = "final", skip_serializing_if = "is_false")]
    pub is_final: bool,
}

fn is_false(b: &bool) -> bool {
    !b
}

/// Result status for edit operations.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ResultStatus {
    Applied,
    Rejected,
    Partial,
    Conflict,
}

/// Description of a single change within a result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangeDescription {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_id: Option<String>,
    pub description: String,
}

/// Content item for `name: "handle"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HandleContentItem {
    pub sections: Vec<SectionDef>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_count: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<ArtifactState>,
}

/// Content item for `name: "result"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResultContentItem {
    pub status: ResultStatus,
    pub mode_used: Name,
    pub changes: Vec<ChangeDescription>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub rejection_reason: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub conflict_detail: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub checksum: Option<String>,
}
