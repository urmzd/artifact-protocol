//! Versioned artifact store — maintains artifact history for diff/section
//! application and rollback support.

use std::collections::HashMap;

use anyhow::{bail, Context, Result};

use crate::apply;
use crate::aap::{Envelope, Mode};

/// Entry in the version history.
#[derive(Debug, Clone)]
struct VersionEntry {
    version: u64,
    content: String,
}

/// In-memory versioned artifact store.
///
/// Maintains a history of resolved content for each artifact ID,
/// enabling diff application, version chain integrity checks, and rollback.
#[derive(Debug, Default)]
pub struct ArtifactStore {
    /// artifact_id -> version history (oldest first)
    history: HashMap<String, Vec<VersionEntry>>,
    /// Maximum versions to keep per artifact
    max_history: usize,
}

impl ArtifactStore {
    pub fn new(max_history: usize) -> Self {
        Self {
            history: HashMap::new(),
            max_history,
        }
    }

    /// Get the current content for an artifact.
    pub fn get(&self, id: &str) -> Option<&str> {
        self.history
            .get(id)
            .and_then(|v| v.last())
            .map(|e| e.content.as_str())
    }

    /// Get the current version number for an artifact.
    pub fn current_version(&self, id: &str) -> Option<u64> {
        self.history
            .get(id)
            .and_then(|v| v.last())
            .map(|e| e.version)
    }

    /// Build a content map for use with `apply::resolve`.
    pub fn content_map(&self) -> HashMap<String, String> {
        self.history
            .iter()
            .filter_map(|(id, v)| v.last().map(|e| (id.clone(), e.content.clone())))
            .collect()
    }

    /// Apply an envelope, resolving its content and storing the result.
    ///
    /// Enforces version chain integrity: for non-full modes, `base_version`
    /// must match the current stored version.
    pub fn apply(&mut self, envelope: &Envelope) -> Result<String> {
        // Version chain check for incremental modes
        if envelope.mode != Mode::Full {
            let base = envelope
                .base_version
                .context("non-full mode requires base_version")?;
            if let Some(current) = self.current_version(&envelope.id) {
                if base != current {
                    bail!(
                        "version conflict: envelope base_version={base}, store has version={current}"
                    );
                }
            } else {
                bail!(
                    "no base content for artifact '{}' — full mode required first",
                    envelope.id
                );
            }
        }

        let store_map = self.content_map();
        let resolved = apply::resolve(envelope, &store_map)?;

        let entries = self.history.entry(envelope.id.clone()).or_default();
        entries.push(VersionEntry {
            version: envelope.version,
            content: resolved.clone(),
        });

        // Trim old versions
        while entries.len() > self.max_history {
            entries.remove(0);
        }

        Ok(resolved)
    }

    /// Roll back to a previous version. Returns the restored content.
    pub fn rollback(&mut self, id: &str, target_version: u64) -> Result<String> {
        let entries = self
            .history
            .get_mut(id)
            .context("artifact not found")?;

        let idx = entries
            .iter()
            .position(|e| e.version == target_version)
            .with_context(|| format!("version {target_version} not in history"))?;

        let content = entries[idx].content.clone();
        let new_version = entries.last().map(|e| e.version).unwrap_or(0) + 1;

        entries.push(VersionEntry {
            version: new_version,
            content: content.clone(),
        });

        while entries.len() > self.max_history {
            entries.remove(0);
        }

        Ok(content)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aap::*;

    fn full_envelope(id: &str, version: u64, content: &str) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(),
            version,
            format: "text/html".to_string(),
            mode: Mode::Full,
            encoding: None,
            base_version: None,
            created_at: None,
            updated_at: None,
            token_budget: None,
            tokens_used: None,
            checksum: None,
            sections: None,
            content: Some(content.to_string()),
            operations: None,
            target_sections: None,
            template: None,
            bindings: None,
            includes: None,
            skeleton: None,
            section_prompts: None,
            section_id: None,
            content_encoding: None,
            rendering: None,
            state: None,
            state_changed_at: None,
            entity: None,
            lock: None,
        }
    }

    fn diff_envelope(id: &str, base_version: u64, version: u64, ops: Vec<DiffOp>) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(),
            version,
            format: "text/html".to_string(),
            mode: Mode::Diff,
            encoding: None,
            base_version: Some(base_version),
            created_at: None,
            updated_at: None,
            token_budget: None,
            tokens_used: None,
            checksum: None,
            sections: None,
            content: None,
            operations: Some(ops),
            target_sections: None,
            template: None,
            bindings: None,
            includes: None,
            skeleton: None,
            section_prompts: None,
            section_id: None,
            content_encoding: None,
            rendering: None,
            state: None,
            state_changed_at: None,
            entity: None,
            lock: None,
        }
    }

    #[test]
    fn test_full_then_diff() {
        let mut store = ArtifactStore::new(10);

        let env1 = full_envelope("test", 1, "<div>hello world</div>");
        let content = store.apply(&env1).unwrap();
        assert_eq!(content, "<div>hello world</div>");

        let env2 = diff_envelope(
            "test",
            1,
            2,
            vec![DiffOp {
                op: OpType::Replace,
                target: Target {
                    search: Some("hello world".to_string()),
                    lines: None,
                    offsets: None,
                    section: None,
                },
                content: Some("hello protocol".to_string()),
            }],
        );
        let content = store.apply(&env2).unwrap();
        assert_eq!(content, "<div>hello protocol</div>");
        assert_eq!(store.current_version("test"), Some(2));
    }

    #[test]
    fn test_version_conflict() {
        let mut store = ArtifactStore::new(10);
        store
            .apply(&full_envelope("test", 1, "content"))
            .unwrap();

        let bad_env = diff_envelope(
            "test",
            5, // wrong base version
            6,
            vec![],
        );
        assert!(store.apply(&bad_env).is_err());
    }

    #[test]
    fn test_rollback() {
        let mut store = ArtifactStore::new(10);
        store
            .apply(&full_envelope("test", 1, "version one"))
            .unwrap();
        store
            .apply(&full_envelope("test", 2, "version two"))
            .unwrap();

        let rolled = store.rollback("test", 1).unwrap();
        assert_eq!(rolled, "version one");
        assert_eq!(store.current_version("test"), Some(3));
    }
}
