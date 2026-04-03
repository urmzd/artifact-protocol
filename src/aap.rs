//! Agent-Artifact Protocol (AAP) data model — Rust implementation of aap/0.1.
//!
//! Three envelope types: `synthesize` (in), `edit` (in), `handle` (out).
//! Artifact is a standalone content object, not an envelope.

use serde::{Deserialize, Serialize};

pub const PROTOCOL_VERSION: &str = "aap/0.1";

/// Envelope operation name — 2 in, 1 out.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Name {
    Synthesize,
    Edit,
    Handle,
}

/// Artifact lifecycle state.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ArtifactState {
    Draft,
    Published,
    Archived,
}

/// Envelope metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Meta {
    pub direction: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub checksum: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<ArtifactState>,
}

/// Wire-format protocol message.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    pub protocol: String,
    pub id: String,
    pub version: u64,
    pub name: Name,
    pub meta: Meta,
    pub content: Vec<serde_json::Value>,
}

impl Envelope {
    pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(s)
    }
}

// ── Artifact ─────────────────────────────────────────────────────────────

/// The actual content being managed — not an envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub id: String,
    pub version: u64,
    pub format: String,
    pub body: String,
}

// ── Synthesize content ───────────────────────────────────────────────────

/// Content item for `name: "synthesize"`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SynthesizeContentItem {
    pub body: String,
}

// ── Edit content ─────────────────────────────────────────────────────────

/// Target addressing — discriminated union on `type`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "value")]
pub enum Target {
    #[serde(rename = "id")]
    Id(String),

    #[serde(rename = "pointer")]
    Pointer(String),
}

/// Edit operation type.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum OpType {
    Replace,
    InsertBefore,
    InsertAfter,
    Delete,
}

/// A single edit operation (content item for `name: "edit"`).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EditOp {
    pub op: OpType,
    pub target: Target,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
}

// ── Handle content ───────────────────────────────────────────────────────

/// Content item for `name: "handle"` — lightweight artifact reference.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HandleContentItem {
    pub id: String,
    pub version: u64,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_count: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<ArtifactState>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
}
