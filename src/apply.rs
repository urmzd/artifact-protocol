//! Stateless apply engine — pure function that transforms artifacts.
//!
//! `apply(artifact?, envelope) → (Artifact, Handle)`
//!
//! Synthesize: creates artifact from body. Edit: applies ops to existing artifact.
//! Both return the artifact and a handle envelope.

use anyhow::{bail, Context, Result};

use crate::gap::{
    Artifact, EditOp, Envelope, HandleContentItem, Name, OpType, Meta, SynthesizeContentItem,
    Target, TargetInfo, PROTOCOL_VERSION,
};

// ── Resolve trait ────────────────────────────────────────────────────────

/// Content resolution — how to find and replace targeted regions.
pub trait Resolve {
    type Content: Clone;

    fn find_by_id(&self, content: &Self::Content, id: &str) -> Result<(usize, usize)>;
    fn find_by_id_inclusive(&self, content: &Self::Content, id: &str) -> Result<(usize, usize)>;
    fn find_by_pointer(&self, content: &Self::Content, pointer: &str) -> Result<(usize, usize)>;
    fn replace(&self, content: &mut Self::Content, start: usize, end: usize, replacement: &str);
    fn insert(&self, content: &mut Self::Content, pos: usize, text: &str);
    fn delete(&self, content: &mut Self::Content, start: usize, end: usize);
    fn to_string(&self, content: &Self::Content) -> String;
    fn from_string(&self, s: &str) -> Self::Content;
}

// ── Text resolver ────────────────────────────────────────────────────────

/// Text-based resolver using `<gap:target id="...">` markers.
pub struct TextResolver {
    pub format: String,
}

impl Resolve for TextResolver {
    type Content = String;

    fn find_by_id(&self, content: &String, id: &str) -> Result<(usize, usize)> {
        crate::markers::find_target_range(content, id, &self.format)
    }

    fn find_by_id_inclusive(&self, content: &String, id: &str) -> Result<(usize, usize)> {
        crate::markers::find_target_range_inclusive(content, id, &self.format)
    }

    fn find_by_pointer(&self, content: &String, pointer: &str) -> Result<(usize, usize)> {
        let value: serde_json::Value = serde_json::from_str(content)
            .context("pointer targeting requires valid JSON content")?;
        let serialized = serde_json::to_string_pretty(&value)?;
        let _ = value
            .pointer(pointer)
            .with_context(|| format!("pointer not found: {pointer}"))?;
        Ok((0, serialized.len()))
    }

    fn replace(&self, content: &mut String, start: usize, end: usize, replacement: &str) {
        *content = format!("{}{}{}", &content[..start], replacement, &content[end..]);
    }

    fn insert(&self, content: &mut String, pos: usize, text: &str) {
        *content = format!("{}{}{}", &content[..pos], text, &content[pos..]);
    }

    fn delete(&self, content: &mut String, start: usize, end: usize) {
        *content = format!("{}{}", &content[..start], &content[end..]);
    }

    fn to_string(&self, content: &String) -> String {
        content.clone()
    }

    fn from_string(&self, s: &str) -> String {
        s.to_string()
    }
}

// ── Apply engine ─────────────────────────────────────────────────────────

fn extract_synthesize_item(envelope: &Envelope) -> Result<SynthesizeContentItem> {
    serde_json::from_value(
        envelope
            .content
            .first()
            .context("synthesize: empty content array")?
            .clone(),
    )
    .context("synthesize: failed to parse content item")
}

fn build_handle_envelope(artifact: &Artifact) -> Result<Envelope> {
    let target_ids = crate::markers::extract_targets(&artifact.body, &artifact.format);
    let targets = if target_ids.is_empty() {
        None
    } else {
        Some(target_ids.into_iter().map(|id| TargetInfo {
            id,
            label: None,
            accepts: None,
        }).collect())
    };
    let handle = HandleContentItem {
        id: artifact.id.clone(),
        version: artifact.version,
        token_count: Some(artifact.body.len() as u64 / 4), // rough estimate
        state: None,
        content: None,
        targets,
    };
    Ok(Envelope {
        protocol: PROTOCOL_VERSION.to_string(),
        id: artifact.id.clone(),
        version: artifact.version,
        name: Name::Handle,
        meta: Meta {
            format: Some(artifact.format.clone()),
            tokens_used: None,
            checksum: None,
            state: None,
        },
        content: vec![
            serde_json::to_value(handle).context("failed to serialize handle")?
        ],
    })
}

/// Stateless apply: `f(artifact?, envelope) → (Artifact, Handle)`.
pub fn apply(artifact: Option<&Artifact>, envelope: &Envelope) -> Result<(Artifact, Envelope)> {
    let format = envelope
        .meta
        .format
        .as_deref()
        .unwrap_or("text/html");

    let resolver = TextResolver {
        format: format.to_string(),
    };

    let result_artifact = match envelope.name {
        Name::Synthesize => {
            let item = extract_synthesize_item(envelope)?;
            Artifact {
                id: envelope.id.clone(),
                version: envelope.version,
                format: format.to_string(),
                body: item.body,
            }
        }
        Name::Edit => {
            let art = artifact.context("edit requires a base artifact")?;
            let ops: Vec<EditOp> = envelope
                .content
                .iter()
                .map(|v| serde_json::from_value(v.clone()))
                .collect::<std::result::Result<Vec<_>, _>>()
                .context("edit: failed to parse content items")?;

            let has_pointer = ops.iter().any(|op| matches!(op.target, Target::Pointer(_)));
            let body = if has_pointer {
                apply_edit_pointers(&art.body, &ops)?
            } else {
                apply_edit(&resolver, &art.body, &ops)?
            };

            Artifact {
                id: envelope.id.clone(),
                version: envelope.version,
                format: format.to_string(),
                body,
            }
        }
        Name::Handle => {
            bail!("handle is an output envelope, not an input operation")
        }
    };

    let handle = build_handle_envelope(&result_artifact)?;
    Ok((result_artifact, handle))
}

/// Apply edit operations using the Resolve trait (ID-based targeting).
pub fn apply_edit<R: Resolve<Content = String>>(
    resolver: &R,
    base: &str,
    operations: &[EditOp],
) -> Result<String> {
    let mut content = resolver.from_string(base);

    for (i, op) in operations.iter().enumerate() {
        // All ops target content between markers (exclusive range).
        // Delete clears the content but preserves markers per spec §4.2.
        let (start, end) = resolve_target(resolver, &content, &op.target)
            .with_context(|| format!("operation {i}: target not found"))?;
        match op.op {
            OpType::Replace => {
                let replacement = op.content.as_deref().unwrap_or("");
                resolver.replace(&mut content, start, end, replacement);
            }
            OpType::Delete => {
                resolver.delete(&mut content, start, end);
            }
            OpType::InsertBefore => {
                let text = op.content.as_deref().unwrap_or("");
                resolver.insert(&mut content, start, text);
            }
            OpType::InsertAfter => {
                let text = op.content.as_deref().unwrap_or("");
                resolver.insert(&mut content, end, text);
            }
        }
    }

    Ok(resolver.to_string(&content))
}

fn resolve_target<R: Resolve<Content = String>>(
    resolver: &R,
    content: &String,
    target: &Target,
) -> Result<(usize, usize)> {
    match target {
        Target::Id(id) => resolver.find_by_id(content, id),
        Target::Pointer(pointer) => resolver.find_by_pointer(content, pointer),
    }
}

/// Apply edit operations using JSON Pointer targeting.
fn apply_edit_pointers(base: &str, operations: &[EditOp]) -> Result<String> {
    let mut value: serde_json::Value =
        serde_json::from_str(base).context("pointer targeting requires valid JSON content")?;

    for (i, op) in operations.iter().enumerate() {
        let pointer = match &op.target {
            Target::Pointer(p) => p.as_str(),
            _ => bail!("operation {i}: expected pointer target"),
        };

        match op.op {
            OpType::Replace => {
                let content = op.content.as_deref().context("replace requires content")?;
                let new_val: serde_json::Value =
                    serde_json::from_str(content).context("content must be valid JSON")?;
                let target = value
                    .pointer_mut(pointer)
                    .with_context(|| format!("pointer not found: {pointer}"))?;
                *target = new_val;
            }
            OpType::Delete => {
                let (parent_ptr, key) = split_pointer(pointer).context("cannot delete root")?;
                let parent = value
                    .pointer_mut(&parent_ptr)
                    .with_context(|| format!("parent not found: {parent_ptr}"))?;
                remove_child(parent, &key)?;
            }
            OpType::InsertBefore | OpType::InsertAfter => {
                let content = op.content.as_deref().context("insert requires content")?;
                let new_val: serde_json::Value =
                    serde_json::from_str(content).context("content must be valid JSON")?;
                let (parent_ptr, key) = split_pointer(pointer).context("cannot insert at root")?;
                let parent = value
                    .pointer_mut(&parent_ptr)
                    .with_context(|| format!("parent not found: {parent_ptr}"))?;
                let arr = parent
                    .as_array_mut()
                    .context("insert requires array parent")?;
                let index: usize = key.parse().context("insert requires numeric array index")?;
                let insert_at = if op.op == OpType::InsertAfter { index + 1 } else { index };
                arr.insert(insert_at, new_val);
            }
        }
    }

    serde_json::to_string_pretty(&value).context("failed to re-serialize JSON")
}

fn split_pointer(pointer: &str) -> Result<(String, String)> {
    if pointer.is_empty() || !pointer.starts_with('/') {
        bail!("invalid JSON Pointer: {pointer:?}");
    }
    match pointer.rfind('/') {
        Some(0) => Ok(("".to_string(), pointer[1..].to_string())),
        Some(pos) => Ok((pointer[..pos].to_string(), pointer[pos + 1..].to_string())),
        None => bail!("invalid JSON Pointer: {pointer:?}"),
    }
}

fn remove_child(parent: &mut serde_json::Value, key: &str) -> Result<()> {
    let unescaped = key.replace("~1", "/").replace("~0", "~");
    if let Some(obj) = parent.as_object_mut() {
        if obj.remove(&unescaped).is_none() {
            bail!("key not found: {unescaped}");
        }
    } else if let Some(arr) = parent.as_array_mut() {
        let index: usize = unescaped.parse().with_context(|| format!("expected array index: {unescaped}"))?;
        if index >= arr.len() { bail!("array index out of bounds: {index}"); }
        arr.remove(index);
    } else {
        bail!("parent is neither object nor array");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn synth_env(id: &str, version: u64, body: &str) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(),
            version,
            name: Name::Synthesize,
            meta: Meta {
                    format: Some("text/html".to_string()),
                tokens_used: None, checksum: None, state: None,
            },
            content: vec![serde_json::json!({ "body": body })],
        }
    }

    fn edit_env(id: &str, version: u64, ops: Vec<EditOp>) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(),
            version,
            name: Name::Edit,
            meta: Meta {
                    format: Some("text/html".to_string()),
                tokens_used: None, checksum: None, state: None,
            },
            content: ops.iter().map(|o| serde_json::to_value(o).unwrap()).collect(),
        }
    }

    fn id_target(id: &str) -> Target { Target::Id(id.to_string()) }
    fn ptr_target(p: &str) -> Target { Target::Pointer(p.to_string()) }

    #[test]
    fn test_synthesize() {
        let env = synth_env("test", 1, "<div>hello</div>");
        let (art, handle) = apply(None, &env).unwrap();
        assert_eq!(art.body, "<div>hello</div>");
        assert_eq!(art.id, "test");
        assert_eq!(art.version, 1);
        assert_eq!(handle.name, Name::Handle);
    }

    #[test]
    fn test_edit_replace_by_id() {
        let env = synth_env("t", 1, r#"<gap:target id="rev">$12,340</gap:target>"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace,
            target: id_target("rev"),
            content: Some("$15,720".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("$15,720"));
        assert!(!art2.body.contains("$12,340"));
        assert!(art2.body.contains(r#"<gap:target id="rev">"#));
    }

    #[test]
    fn test_edit_delete_by_id() {
        // Spec §4.2: "For delete, the content between markers is removed
        // (markers are preserved). Markers themselves are never moved or
        // removed by edit operations."
        let env = synth_env("t", 1, r#"before<gap:target id="tmp">remove</gap:target>after"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: id_target("tmp"), content: None,
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert_eq!(art2.body, r#"before<gap:target id="tmp"></gap:target>after"#);
    }

    #[test]
    fn test_edit_insert_after() {
        let env = synth_env("t", 1, r#"<gap:target id="list">item1</gap:target>"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::InsertAfter, target: id_target("list"),
            content: Some(", item2".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("item1, item2"));
    }

    #[test]
    fn test_nested_targets() {
        let body = r#"<gap:target id="outer"><h2>Stats</h2><gap:target id="val">100</gap:target></gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("val"),
            content: Some("200".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("200"));
        assert!(art2.body.contains("<h2>Stats</h2>"));
    }

    #[test]
    fn test_target_serde_roundtrip() {
        let t = Target::Id("revenue".to_string());
        let json = serde_json::to_string(&t).unwrap();
        let parsed: Target = serde_json::from_str(&json).unwrap();
        assert!(matches!(parsed, Target::Id(ref s) if s == "revenue"));

        let op = EditOp {
            op: OpType::Replace,
            target: Target::Id("rev".to_string()),
            content: Some("new".to_string()),
        };
        let json = serde_json::to_string(&op).unwrap();
        let parsed: EditOp = serde_json::from_str(&json).unwrap();
        assert!(matches!(parsed.target, Target::Id(ref s) if s == "rev"));
    }

    #[test]
    fn test_edit_from_json_string() {
        let json = r#"{
            "protocol": "gap/0.1", "id": "x", "version": 2, "name": "edit",
            "meta": {"format": "text/html"},
            "content": [{"op": "replace", "target": {"type": "id", "value": "rev"}, "content": "new"}]
        }"#;
        let env: Envelope = serde_json::from_str(json).unwrap();
        let art_body = r#"<gap:target id="rev">old</gap:target>"#;
        let (art, _) = apply(None, &synth_env("x", 1, art_body)).unwrap();
        let (art2, _) = apply(Some(&art), &env).unwrap();
        assert!(art2.body.contains("new"));
        assert!(!art2.body.contains("old"));
    }

    #[test]
    fn test_pointer_replace() {
        let base = r#"{"name": "Alice", "age": 30}"#;
        let (art, _) = apply(None, &synth_env("t", 1, base)).unwrap();

        let mut edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/name"),
            content: Some(r#""Bob""#.to_string()),
        }]);
        edit.meta.format = Some("application/json".to_string());
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(parsed["name"], "Bob");
        assert_eq!(parsed["age"], 30);
    }

    #[test]
    fn test_pointer_delete() {
        let base = r#"{"name": "Alice", "temp": true}"#;
        let (art, _) = apply(None, &synth_env("t", 1, base)).unwrap();

        let mut edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: ptr_target("/temp"), content: None,
        }]);
        edit.meta.format = Some("application/json".to_string());
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert!(parsed.get("temp").is_none());
    }

    #[test]
    fn test_handle_is_not_input() {
        let env = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "t".to_string(), version: 1, name: Name::Handle,
            meta: Meta {
                format: None,
                tokens_used: None, checksum: None, state: None,
            },
            content: vec![],
        };
        assert!(apply(None, &env).is_err());
    }

    #[test]
    fn test_synthesize_returns_targets() {
        let body = r#"<gap:target id="stats"><gap:target id="rev">$100</gap:target></gap:target>"#;
        let (_, handle) = apply(None, &synth_env("t", 1, body)).unwrap();
        let item: crate::gap::HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        let targets = item.targets.unwrap();
        let ids: Vec<&str> = targets.iter().map(|t| t.id.as_str()).collect();
        assert_eq!(ids, vec!["stats", "rev"]);
    }

    #[test]
    fn test_nested_target_invalidation() {
        let body = r#"<gap:target id="outer"><gap:target id="inner">v</gap:target></gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        // Replace outer with content that drops inner
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("outer"),
            content: Some("no nested targets here".to_string()),
        }]);
        let (_, handle) = apply(Some(&art), &edit).unwrap();
        let item: crate::gap::HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        let targets = item.targets.unwrap();
        let ids: Vec<&str> = targets.iter().map(|t| t.id.as_str()).collect();
        // outer still exists (markers preserved), but inner is gone
        assert_eq!(ids, vec!["outer"]);
    }

    #[test]
    fn test_no_targets_for_json() {
        let base = r#"{"key": "value"}"#;
        let mut env = synth_env("t", 1, base);
        env.meta.format = Some("application/json".to_string());
        let (_, handle) = apply(None, &env).unwrap();
        let item: crate::gap::HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        assert!(item.targets.is_none());
    }

    // ── ID-based edge cases ────────────────────────────────────────────

    #[test]
    fn test_edit_insert_before() {
        let env = synth_env("t", 1, r#"<gap:target id="list">item1</gap:target>"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::InsertBefore, target: id_target("list"),
            content: Some("item0, ".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("item0, item1"));
        assert!(art2.body.contains(r#"<gap:target id="list">"#));
    }

    #[test]
    fn test_replace_with_empty_string() {
        let env = synth_env("t", 1, r#"<gap:target id="val">old</gap:target>"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("val"),
            content: Some("".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert_eq!(art2.body, r#"<gap:target id="val"></gap:target>"#);
    }

    #[test]
    fn test_replace_with_none_content() {
        let env = synth_env("t", 1, r#"<gap:target id="val">old</gap:target>"#);
        let (art, _) = apply(None, &env).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("val"),
            content: None,
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert_eq!(art2.body, r#"<gap:target id="val"></gap:target>"#);
    }

    #[test]
    fn test_delete_preserves_markers_for_reuse() {
        // After delete, the target should still be addressable for future ops.
        let body = r#"<gap:target id="msg">hello</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let delete = edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: id_target("msg"), content: None,
        }]);
        let (art2, _) = apply(Some(&art), &delete).unwrap();
        assert!(art2.body.contains(r#"<gap:target id="msg">"#));
        assert!(art2.body.contains("</gap:target>"));
        assert!(!art2.body.contains("hello"));

        // Can still replace into the now-empty target.
        let replace = edit_env("t", 3, vec![EditOp {
            op: OpType::Replace, target: id_target("msg"),
            content: Some("world".to_string()),
        }]);
        let (art3, _) = apply(Some(&art2), &replace).unwrap();
        assert!(art3.body.contains("world"));
    }

    #[test]
    fn test_delete_target_still_in_handle() {
        // Since markers are preserved, handle should still list the target.
        let body = r#"<gap:target id="msg">hello</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let delete = edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: id_target("msg"), content: None,
        }]);
        let (_, handle) = apply(Some(&art), &delete).unwrap();
        let item: crate::gap::HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        let targets = item.targets.unwrap();
        let ids: Vec<&str> = targets.iter().map(|t| t.id.as_str()).collect();
        assert_eq!(ids, vec!["msg"]);
    }

    #[test]
    fn test_multiple_ops_same_target() {
        // Delete content, then insert new content into same target.
        let body = r#"<gap:target id="x">old</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![
            EditOp { op: OpType::Delete, target: id_target("x"), content: None },
            EditOp { op: OpType::InsertAfter, target: id_target("x"), content: Some("new".to_string()) },
        ]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("new"));
        assert!(!art2.body.contains("old"));
    }

    #[test]
    fn test_multiple_ops_different_targets() {
        let body = r#"<gap:target id="a">1</gap:target><gap:target id="b">2</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![
            EditOp { op: OpType::Replace, target: id_target("a"), content: Some("X".to_string()) },
            EditOp { op: OpType::Replace, target: id_target("b"), content: Some("Y".to_string()) },
        ]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("X"));
        assert!(art2.body.contains("Y"));
        assert!(!art2.body.contains("1"));
        assert!(!art2.body.contains("2"));
    }

    #[test]
    fn test_nonexistent_target_fails() {
        let body = r#"<gap:target id="a">val</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("nonexistent"),
            content: Some("x".to_string()),
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_deeply_nested_targets() {
        let body = r#"<gap:target id="l1"><gap:target id="l2"><gap:target id="l3">deep</gap:target></gap:target></gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        // Edit the innermost target.
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("l3"),
            content: Some("shallow".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("shallow"));
        // Outer markers still intact.
        assert!(art2.body.contains(r#"<gap:target id="l1">"#));
        assert!(art2.body.contains(r#"<gap:target id="l2">"#));
    }

    #[test]
    fn test_adjacent_sibling_targets() {
        let body = r#"<gap:target id="a">1</gap:target><gap:target id="b">2</gap:target><gap:target id="c">3</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        // Replace middle sibling.
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("b"),
            content: Some("X".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains(r#"<gap:target id="a">1</gap:target>"#));
        assert!(art2.body.contains(r#"<gap:target id="b">X</gap:target>"#));
        assert!(art2.body.contains(r#"<gap:target id="c">3</gap:target>"#));
    }

    #[test]
    fn test_replace_with_content_containing_new_targets() {
        let body = r#"<gap:target id="section">old</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let new_content = r#"<gap:target id="inner">nested</gap:target>"#;
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("section"),
            content: Some(new_content.to_string()),
        }]);
        let (_, handle) = apply(Some(&art), &edit).unwrap();
        let item: crate::gap::HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        let targets = item.targets.unwrap();
        let ids: Vec<&str> = targets.iter().map(|t| t.id.as_str()).collect();
        assert_eq!(ids, vec!["section", "inner"]);
    }

    #[test]
    fn test_empty_target_content() {
        let body = r#"<gap:target id="empty"></gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::InsertAfter, target: id_target("empty"),
            content: Some("filled".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("filled"));
    }

    #[test]
    fn test_edit_without_base_artifact_fails() {
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("x"),
            content: Some("y".to_string()),
        }]);
        assert!(apply(None, &edit).is_err());
    }

    #[test]
    fn test_synthesize_empty_content_array_fails() {
        let env = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "t".to_string(), version: 1, name: Name::Synthesize,
            meta: Meta { format: Some("text/html".to_string()),
                tokens_used: None, checksum: None, state: None },
            content: vec![],
        };
        assert!(apply(None, &env).is_err());
    }

    #[test]
    fn test_edit_empty_ops_is_noop() {
        let body = r#"<gap:target id="a">val</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert_eq!(art2.body, body);
    }

    #[test]
    fn test_default_format_is_html() {
        let env = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "t".to_string(), version: 1, name: Name::Synthesize,
            meta: Meta { format: None, tokens_used: None, checksum: None, state: None },
            content: vec![serde_json::json!({ "body": "<div>hi</div>" })],
        };
        let (art, _) = apply(None, &env).unwrap();
        assert_eq!(art.format, "text/html");
    }

    #[test]
    fn test_synthesize_overwrites_existing_artifact() {
        let (art, _) = apply(None, &synth_env("t", 1, "v1")).unwrap();
        let (art2, _) = apply(Some(&art), &synth_env("t", 2, "v2")).unwrap();
        assert_eq!(art2.body, "v2");
        assert_eq!(art2.version, 2);
    }

    #[test]
    fn test_all_or_nothing_semantics() {
        // Second op targets a nonexistent target — entire edit should fail.
        let body = r#"<gap:target id="a">old</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![
            EditOp { op: OpType::Replace, target: id_target("a"), content: Some("new".to_string()) },
            EditOp { op: OpType::Replace, target: id_target("missing"), content: Some("x".to_string()) },
        ]);
        assert!(apply(Some(&art), &edit).is_err());
        // Original artifact body is unchanged (we still have the immutable ref).
        assert_eq!(art.body, body);
    }

    #[test]
    fn test_sequential_ops_with_position_shift() {
        // Two insert_after ops on the same target — both should work.
        let body = r#"<gap:target id="list">a</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![
            EditOp { op: OpType::InsertAfter, target: id_target("list"), content: Some("b".to_string()) },
            EditOp { op: OpType::InsertAfter, target: id_target("list"), content: Some("c".to_string()) },
        ]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("abc"));
    }

    #[test]
    fn test_insert_before_and_after_combined() {
        let body = r#"<gap:target id="mid">M</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![
            EditOp { op: OpType::InsertBefore, target: id_target("mid"), content: Some("B".to_string()) },
            EditOp { op: OpType::InsertAfter, target: id_target("mid"), content: Some("A".to_string()) },
        ]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("BMA"));
    }

    #[test]
    fn test_delete_nested_inner_preserves_outer() {
        let body = r#"<gap:target id="outer">pre<gap:target id="inner">val</gap:target>post</gap:target>"#;
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: id_target("inner"), content: None,
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        // Inner markers preserved but content gone, outer intact.
        assert!(art2.body.contains(r#"<gap:target id="inner"></gap:target>"#));
        assert!(art2.body.contains("pre"));
        assert!(art2.body.contains("post"));
        assert!(art2.body.contains(r#"<gap:target id="outer">"#));
    }

    #[test]
    fn test_handle_version_matches_envelope() {
        let env = synth_env("t", 5, "<div>hi</div>");
        let (art, handle) = apply(None, &env).unwrap();
        assert_eq!(art.version, 5);
        assert_eq!(handle.version, 5);
    }

    #[test]
    fn test_handle_id_matches_envelope() {
        let env = synth_env("my-artifact", 1, "body");
        let (_, handle) = apply(None, &env).unwrap();
        assert_eq!(handle.id, "my-artifact");
    }

    #[test]
    fn test_multiline_content_in_targets() {
        let body = "<gap:target id=\"code\">line1\nline2\nline3</gap:target>";
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("code"),
            content: Some("replaced\ncontent".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("replaced\ncontent"));
        assert!(!art2.body.contains("line1"));
    }

    // ── Pointer-based edge cases ───────────────────────────────────────

    fn json_edit_env(id: &str, version: u64, ops: Vec<EditOp>) -> Envelope {
        let mut env = edit_env(id, version, ops);
        env.meta.format = Some("application/json".to_string());
        env
    }

    fn json_synth_env(id: &str, version: u64, body: &str) -> Envelope {
        let mut env = synth_env(id, version, body);
        env.meta.format = Some("application/json".to_string());
        env
    }

    #[test]
    fn test_pointer_nested_path() {
        let base = r#"{"a": {"b": {"c": 1}}}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/a/b/c"),
            content: Some("42".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["a"]["b"]["c"], 42);
    }

    #[test]
    fn test_pointer_replace_array_element() {
        let base = r#"{"items": [10, 20, 30]}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/items/1"),
            content: Some("99".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["items"], serde_json::json!([10, 99, 30]));
    }

    #[test]
    fn test_pointer_delete_array_element() {
        let base = r#"{"items": [1, 2, 3]}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: ptr_target("/items/1"), content: None,
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["items"], serde_json::json!([1, 3]));
    }

    #[test]
    fn test_pointer_insert_before_array() {
        let base = r#"{"items": [1, 2, 3]}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::InsertBefore, target: ptr_target("/items/1"),
            content: Some("99".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["items"], serde_json::json!([1, 99, 2, 3]));
    }

    #[test]
    fn test_pointer_insert_after_array() {
        let base = r#"{"items": [1, 2, 3]}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::InsertAfter, target: ptr_target("/items/1"),
            content: Some("99".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["items"], serde_json::json!([1, 2, 99, 3]));
    }

    #[test]
    fn test_pointer_multiple_ops() {
        let base = r#"{"name": "Alice", "age": 30, "city": "NYC"}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![
            EditOp { op: OpType::Replace, target: ptr_target("/name"), content: Some(r#""Bob""#.to_string()) },
            EditOp { op: OpType::Delete, target: ptr_target("/city"), content: None },
        ]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["name"], "Bob");
        assert_eq!(v["age"], 30);
        assert!(v.get("city").is_none());
    }

    #[test]
    fn test_pointer_nonexistent_path_fails() {
        let base = r#"{"a": 1}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/nonexistent"),
            content: Some("1".to_string()),
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_rfc6901_escaping() {
        // RFC 6901: ~0 = ~, ~1 = /
        let base = r#"{"a/b": 1, "c~d": 2}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/a~1b"),
            content: Some("10".to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["a/b"], 10);

        let edit2 = json_edit_env("t", 3, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/c~0d"),
            content: Some("20".to_string()),
        }]);
        let (art3, _) = apply(Some(&art2), &edit2).unwrap();
        let v2: serde_json::Value = serde_json::from_str(&art3.body).unwrap();
        assert_eq!(v2["c~d"], 20);
    }

    #[test]
    fn test_pointer_insert_on_object_fails() {
        // Insert requires array parent per spec.
        let base = r#"{"a": {"b": 1}}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::InsertBefore, target: ptr_target("/a/b"),
            content: Some("2".to_string()),
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_delete_root_fails() {
        let base = r#"{"a": 1}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: ptr_target(""), content: None,
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_array_out_of_bounds_fails() {
        let base = r#"{"items": [1, 2]}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Delete, target: ptr_target("/items/5"), content: None,
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_replace_with_complex_value() {
        let base = r#"{"config": null}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/config"),
            content: Some(r#"{"host": "localhost", "port": 5432}"#.to_string()),
        }]);
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        let v: serde_json::Value = serde_json::from_str(&art2.body).unwrap();
        assert_eq!(v["config"]["host"], "localhost");
        assert_eq!(v["config"]["port"], 5432);
    }

    #[test]
    fn test_pointer_replace_invalid_json_content_fails() {
        let base = r#"{"a": 1}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/a"),
            content: Some("not valid json".to_string()),
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_on_non_json_content_fails() {
        // Pointer ops require valid JSON body.
        let body = "not json at all";
        let (art, _) = apply(None, &synth_env("t", 1, body)).unwrap();

        let edit = json_edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: ptr_target("/field"),
            content: Some("1".to_string()),
        }]);
        assert!(apply(Some(&art), &edit).is_err());
    }

    #[test]
    fn test_pointer_all_or_nothing() {
        let base = r#"{"a": 1, "b": 2}"#;
        let (art, _) = apply(None, &json_synth_env("t", 1, base)).unwrap();

        let edit = json_edit_env("t", 2, vec![
            EditOp { op: OpType::Replace, target: ptr_target("/a"), content: Some("10".to_string()) },
            EditOp { op: OpType::Replace, target: ptr_target("/missing"), content: Some("1".to_string()) },
        ]);
        assert!(apply(Some(&art), &edit).is_err());
        // Original artifact unchanged.
        let v: serde_json::Value = serde_json::from_str(&art.body).unwrap();
        assert_eq!(v["a"], 1);
    }

    // ── Format handling ────────────────────────────────────────────────

    #[test]
    fn test_python_format_targets() {
        let body = r#"<gap:target id="imports">import os</gap:target>"#;
        let mut env = synth_env("t", 1, body);
        env.meta.format = Some("text/x-python".to_string());
        let (art, _) = apply(None, &env).unwrap();
        assert_eq!(art.format, "text/x-python");

        let mut edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("imports"),
            content: Some("import sys".to_string()),
        }]);
        edit.meta.format = Some("text/x-python".to_string());
        let (art2, _) = apply(Some(&art), &edit).unwrap();
        assert!(art2.body.contains("import sys"));
    }

    // ── Store edge cases ───────────────────────────────────────────────

    #[test]
    fn test_store_edit_without_synthesize_fails() {
        let mut store = crate::store::ArtifactStore::new(10);
        let edit = edit_env("t", 2, vec![EditOp {
            op: OpType::Replace, target: id_target("x"),
            content: Some("y".to_string()),
        }]);
        assert!(store.apply(&edit).is_err());
    }

    #[test]
    fn test_store_multiple_artifacts() {
        let mut store = crate::store::ArtifactStore::new(10);
        store.apply(&synth_env("a", 1, "artifact-a")).unwrap();
        store.apply(&synth_env("b", 1, "artifact-b")).unwrap();
        assert_eq!(store.get("a").unwrap().body, "artifact-a");
        assert_eq!(store.get("b").unwrap().body, "artifact-b");
    }

    #[test]
    fn test_store_max_history_eviction() {
        let mut store = crate::store::ArtifactStore::new(2);
        store.apply(&synth_env("t", 1, "v1")).unwrap();
        store.apply(&synth_env("t", 2, "v2")).unwrap();
        store.apply(&synth_env("t", 3, "v3")).unwrap();
        // Only 2 most recent should remain — rollback to v1 should fail.
        assert!(store.rollback("t", 1).is_err());
        // v2 should still be available.
        let rolled = store.rollback("t", 2).unwrap();
        assert_eq!(rolled.body, "v2");
    }

    #[test]
    fn test_store_synthesize_resets_chain() {
        // Synthesize doesn't require version continuity.
        let mut store = crate::store::ArtifactStore::new(10);
        store.apply(&synth_env("t", 1, "v1")).unwrap();
        // Jump to version 10 via synthesize — should succeed.
        store.apply(&synth_env("t", 10, "v10")).unwrap();
        assert_eq!(store.current_version("t"), Some(10));
    }
}
