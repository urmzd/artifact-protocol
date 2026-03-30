//! Agent-Artifact Protocol (AAP) data model — Rust implementation of aap/1.0.
//!
//! Provides serde-compatible types for envelopes, diff operations, section
//! updates, template bindings, chunk frames, and token budgets.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const PROTOCOL_VERSION: &str = "aap/1.0";

/// Display mode for rendering hints.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum DisplayMode {
    Code,
    Preview,
    Form,
    Dashboard,
    Document,
    Diagram,
    Raw,
    #[serde(untagged)]
    Custom(String),
}

/// Sandbox policy for executable content.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SandboxPolicy {
    #[serde(default, skip_serializing_if = "is_false")]
    pub allow_scripts: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    pub allow_forms: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    pub allow_same_origin: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    pub allow_popups: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    pub allow_modals: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub csp: Option<String>,
}

/// Accessibility hints for artifact rendering.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessibilityHints {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub role: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lang: Option<String>,
}

/// Progressive rendering control.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressiveRendering {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub skeleton_content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reveal: Option<String>,
}

/// Rendering hints for artifact display.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenderingHints {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<DisplayMode>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub language: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub theme: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub line_numbers: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub word_wrap: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_height: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub sandbox: Option<SandboxPolicy>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub accessibility: Option<AccessibilityHints>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub progressive: Option<ProgressiveRendering>,
}

/// Artifact lifecycle state.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ArtifactState {
    Draft,
    Published,
    Archived,
}

/// Access control permissions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Permissions {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub read: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub write: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub admin: Vec<String>,
}

/// Typed relationship to another artifact.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relationship {
    #[serde(rename = "type")]
    pub rel_type: String,
    pub target: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<u64>,
}

/// Entity metadata for managed artifacts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityMetadata {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub owner: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_by: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub permissions: Option<Permissions>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub collection: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ttl: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub relationships: Vec<Relationship>,
}

/// Advisory lock hint for coordinating concurrent editors.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdvisoryLock {
    pub held_by: String,
    pub acquired_at: String,
    pub ttl: u64,
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

/// Top-level envelope wrapping all protocol payloads.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    pub protocol: String,
    pub id: String,
    pub version: u64,
    pub format: String,
    pub mode: Mode,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub base_version: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_at: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated_at: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_budget: Option<TokenBudget>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<u64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub checksum: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub sections: Option<Vec<SectionDef>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub operations: Option<Vec<DiffOp>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub target_sections: Option<Vec<SectionUpdate>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub template: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub bindings: Option<HashMap<String, serde_json::Value>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub includes: Option<Vec<Include>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub skeleton: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_prompts: Option<Vec<SectionPromptDef>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_id: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_encoding: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub rendering: Option<RenderingHints>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<ArtifactState>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub state_changed_at: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub entity: Option<EntityMetadata>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub lock: Option<AdvisoryLock>,
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

/// Generation mode.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Mode {
    Full,
    Diff,
    Section,
    Template,
    Composite,
    Manifest,
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

    #[serde(skip_serializing_if = "Option::is_none")]
    pub rendering: Option<RenderingHints>,
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
}

/// Section content replacement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionUpdate {
    pub id: String,
    pub content: String,
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

/// Streaming chunk frame.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkFrame {
    pub seq: u64,
    pub content: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub envelope: Option<serde_json::Value>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_id: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub rendering: Option<RenderingHints>,

    #[serde(default, skip_serializing_if = "is_false")]
    pub flush: bool,

    #[serde(default, rename = "final", skip_serializing_if = "is_false")]
    pub is_final: bool,
}

fn is_false(b: &bool) -> bool {
    !b
}
