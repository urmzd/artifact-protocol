//! Versioned artifact store — stateful layer over the stateless apply engine.

use std::collections::HashMap;

use anyhow::{bail, Context, Result};
use sha2::{Digest, Sha256};

use crate::gap::{Artifact, Envelope, Name};
use crate::apply;

/// In-memory versioned artifact store.
#[derive(Debug, Default)]
pub struct ArtifactStore {
    history: HashMap<String, Vec<Artifact>>,
    max_history: usize,
}

impl ArtifactStore {
    pub fn new(max_history: usize) -> Self {
        Self {
            history: HashMap::new(),
            max_history,
        }
    }

    pub fn get(&self, id: &str) -> Option<&Artifact> {
        self.history.get(id).and_then(|v| v.last())
    }

    pub fn current_version(&self, id: &str) -> Option<u64> {
        self.get(id).map(|a| a.version)
    }

    /// Apply an envelope. Returns (Artifact, Handle).
    pub fn apply(&mut self, envelope: &Envelope) -> Result<(Artifact, Envelope)> {
        if envelope.name != Name::Synthesize {
            if let Some(current) = self.current_version(&envelope.id) {
                if current != envelope.version - 1 {
                    bail!(
                        "version conflict: stored={current}, envelope={}, expected={}",
                        envelope.version, envelope.version - 1
                    );
                }
            } else {
                bail!("no base artifact for '{}' — synthesize first", envelope.id);
            }
        }

        let artifact = self.get(&envelope.id);
        let (new_artifact, handle) = apply::apply(artifact, envelope)?;

        let entries = self.history.entry(envelope.id.clone()).or_default();
        entries.push(new_artifact.clone());
        while entries.len() > self.max_history {
            entries.remove(0);
        }

        Ok((new_artifact, handle))
    }

    pub fn checksum(&self, id: &str) -> Result<String> {
        let art = self.get(id).context("artifact not found")?;
        let mut hasher = Sha256::new();
        hasher.update(art.body.as_bytes());
        Ok(format!("sha256:{:x}", hasher.finalize()))
    }

    pub fn rollback(&mut self, id: &str, target_version: u64) -> Result<Artifact> {
        let entries = self.history.get_mut(id).context("artifact not found")?;
        let idx = entries
            .iter()
            .position(|a| a.version == target_version)
            .with_context(|| format!("version {target_version} not in history"))?;

        let mut rolled = entries[idx].clone();
        let new_version = entries.last().map(|a| a.version).unwrap_or(0) + 1;
        rolled.version = new_version;
        entries.push(rolled.clone());

        while entries.len() > self.max_history {
            entries.remove(0);
        }

        Ok(rolled)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::gap::*;

    fn make_meta(fmt: &str) -> Meta {
        Meta {
            format: Some(fmt.to_string()),
            tokens_used: None, checksum: None, state: None,
        }
    }

    fn synth_env(id: &str, version: u64, body: &str) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(), version,
            name: Name::Synthesize,
            meta: make_meta("text/html"),
            content: vec![serde_json::json!({ "body": body })],
        }
    }

    fn edit_env(id: &str, version: u64, ops: Vec<EditOp>) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(), version,
            name: Name::Edit,
            meta: make_meta("text/html"),
            content: ops.iter().map(|o| serde_json::to_value(o).unwrap()).collect(),
        }
    }

    #[test]
    fn test_synthesize_then_edit() {
        let mut store = ArtifactStore::new(10);

        let (art, handle) = store.apply(&synth_env("t", 1, r#"<gap:target id="msg">hello</gap:target>"#)).unwrap();
        assert_eq!(art.body.contains("hello"), true);
        assert_eq!(handle.name, Name::Handle);

        let (art2, _) = store.apply(&edit_env("t", 2, vec![EditOp {
            op: OpType::Replace,
            target: Target::Id("msg".to_string()),
            content: Some("world".to_string()),
        }])).unwrap();
        assert!(art2.body.contains("world"));
        assert_eq!(store.current_version("t"), Some(2));
    }

    #[test]
    fn test_version_conflict() {
        let mut store = ArtifactStore::new(10);
        store.apply(&synth_env("t", 1, "content")).unwrap();
        assert!(store.apply(&edit_env("t", 6, vec![])).is_err());
    }

    #[test]
    fn test_rollback() {
        let mut store = ArtifactStore::new(10);
        store.apply(&synth_env("t", 1, "v1")).unwrap();
        store.apply(&synth_env("t", 2, "v2")).unwrap();
        let rolled = store.rollback("t", 1).unwrap();
        assert_eq!(rolled.body, "v1");
        assert_eq!(store.current_version("t"), Some(3));
    }

    #[test]
    fn test_checksum() {
        let mut store = ArtifactStore::new(10);
        store.apply(&synth_env("t", 1, "hello")).unwrap();
        assert!(store.checksum("t").unwrap().starts_with("sha256:"));
    }
}
