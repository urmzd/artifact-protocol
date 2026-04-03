//! Stateless apply engine — pure function that transforms artifacts.
//!
//! Two input operations: `synthesize` (replace) and `edit` (targeted edits by ID or pointer).
//! Returns `(artifact, handle)` — artifact is stored, handle is returned to the orchestrator.

use anyhow::{bail, Context, Result};
use regex::Regex;

use crate::aap::{
    DiffOp, Envelope, HandleContentItem, Name, OpType, Operation, SynthesizeContentItem, Target,
    TargetDef, PROTOCOL_VERSION,
};

// ── Resolve trait ────────────────────────────────────────────────────────────

/// Content resolution — how to find and replace targeted regions.
///
/// Generic over the content type: text (String), bytes (Vec<u8>), AST nodes, etc.
/// The apply engine calls these methods; implementations provide format-specific logic.
pub trait Resolve {
    type Content: Clone;

    /// Find the byte/index range of a target by ID.
    /// Returns `(start, end)` — the content between markers, exclusive of markers.
    fn find_by_id(&self, content: &Self::Content, id: &str) -> Result<(usize, usize)>;

    /// Find the byte/index range of a target by JSON Pointer.
    fn find_by_pointer(&self, content: &Self::Content, pointer: &str) -> Result<(usize, usize)>;

    /// Replace a range with new content.
    fn replace(&self, content: &mut Self::Content, start: usize, end: usize, replacement: &str);

    /// Insert content at a position.
    fn insert(&self, content: &mut Self::Content, pos: usize, text: &str);

    /// Delete a range.
    fn delete(&self, content: &mut Self::Content, start: usize, end: usize);

    /// Extract the full content as a string (for serialization).
    fn to_string(&self, content: &Self::Content) -> String;

    /// Parse content from a string.
    fn from_string(&self, s: &str) -> Self::Content;
}

// ── Text resolver ────────────────────────────────────────────────────────────

/// Text-based resolver using `<aap:target id="...">` markers.
pub struct TextResolver {
    pub format: String,
}

impl Resolve for TextResolver {
    type Content = String;

    fn find_by_id(&self, content: &String, id: &str) -> Result<(usize, usize)> {
        crate::markers::find_target_range(content, id, &self.format)
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

// ── Apply engine ─────────────────────────────────────────────────────────────

/// Extract a `SynthesizeContentItem` from an envelope.
fn extract_synthesize_item(envelope: &Envelope) -> Result<SynthesizeContentItem> {
    serde_json::from_value(
        envelope
            .content
            .first()
            .context("synthesize envelope: empty content array")?
            .clone(),
    )
    .context("synthesize envelope: failed to parse content item")
}

/// Extract all target IDs from content by scanning for `<aap:target id="...">` markers.
fn extract_target_ids(content: &str) -> Vec<String> {
    let re = Regex::new(r#"<aap:target\s+id="([^"]+)">"#).expect("valid regex");
    re.captures_iter(content)
        .map(|cap| cap[1].to_string())
        .collect()
}

/// Build a `name:"synthesize"` output envelope (the stored artifact).
fn build_synthesize_envelope(
    id: &str,
    version: u64,
    format: Option<&str>,
    body: String,
    targets: Option<Vec<TargetDef>>,
) -> Result<Envelope> {
    let content_item = SynthesizeContentItem { body, targets };
    Ok(Envelope {
        protocol: PROTOCOL_VERSION.to_string(),
        id: id.to_string(),
        version,
        name: Name::Synthesize,
        operation: Operation {
            direction: "output".to_string(),
            format: format.map(|s| s.to_string()),
            encoding: None,
            content_encoding: None,
            token_budget: None,
            tokens_used: None,
            checksum: None,
            created_at: None,
            updated_at: None,
            state: None,
            state_changed_at: None,
        },
        content: vec![
            serde_json::to_value(content_item).context("failed to serialize content item")?
        ],
    })
}

/// Build a `name:"handle"` output envelope.
fn build_handle_envelope(
    id: &str,
    version: u64,
    format: Option<&str>,
    sections: Vec<String>,
    token_count: Option<u64>,
) -> Result<Envelope> {
    let content_item = HandleContentItem {
        sections,
        token_count,
        state: None,
    };
    Ok(Envelope {
        protocol: PROTOCOL_VERSION.to_string(),
        id: id.to_string(),
        version,
        name: Name::Handle,
        operation: Operation {
            direction: "output".to_string(),
            format: format.map(|s| s.to_string()),
            encoding: None,
            content_encoding: None,
            token_budget: None,
            tokens_used: None,
            checksum: None,
            created_at: None,
            updated_at: None,
            state: None,
            state_changed_at: None,
        },
        content: vec![
            serde_json::to_value(content_item).context("failed to serialize handle content")?
        ],
    })
}

/// Stateless apply: `f(artifact, operation) → (artifact, handle)`.
///
/// The artifact is the resolved content (stored). The handle is a lightweight
/// reference returned to the orchestrator.
pub fn apply(artifact: Option<&Envelope>, operation: &Envelope) -> Result<(Envelope, Envelope)> {
    let format = operation
        .operation
        .format
        .as_deref()
        .unwrap_or("text/html");

    let resolver = TextResolver {
        format: format.to_string(),
    };

    let (body, targets) = match operation.name {
        Name::Synthesize => {
            let item = extract_synthesize_item(operation)?;
            (item.body, item.targets)
        }
        Name::Edit => {
            let art = artifact.context("edit requires a base artifact")?;
            let art_item = extract_synthesize_item(art)?;
            let ops: Vec<DiffOp> = operation
                .content
                .iter()
                .map(|v| serde_json::from_value(v.clone()))
                .collect::<std::result::Result<Vec<_>, _>>()
                .context("edit: failed to parse content items")?;

            let has_pointer = ops.iter().any(|op| matches!(op.target, Target::Pointer(_)));
            let body = if has_pointer {
                apply_diff_pointers(&art_item.body, &ops)?
            } else {
                apply_diff(&resolver, &art_item.body, &ops)?
            };
            (body, art_item.targets)
        }
        _ => bail!("apply engine only accepts synthesize or edit operations"),
    };

    // Build the stored artifact
    let artifact_envelope =
        build_synthesize_envelope(&operation.id, operation.version, Some(format), body.clone(), targets)?;

    // Build the handle for the orchestrator
    let sections = extract_target_ids(&body);
    let token_count = Some((body.len() / 4) as u64); // approximate tokens
    let handle = build_handle_envelope(
        &operation.id,
        operation.version,
        Some(format),
        sections,
        token_count,
    )?;

    Ok((artifact_envelope, handle))
}

/// Apply diff operations using the Resolve trait (ID-based targeting).
pub fn apply_diff<R: Resolve<Content = String>>(
    resolver: &R,
    base: &str,
    operations: &[DiffOp],
) -> Result<String> {
    let mut content = resolver.from_string(base);

    for (i, op) in operations.iter().enumerate() {
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

/// Resolve a target to a byte range using the resolver.
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

/// Apply diff operations using JSON Pointer targeting.
fn apply_diff_pointers(base: &str, operations: &[DiffOp]) -> Result<String> {
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
                    .context("insert_before/insert_after require array parent")?;
                let index: usize = key
                    .parse()
                    .context("insert_before/insert_after require numeric array index")?;
                let insert_at = if op.op == OpType::InsertAfter {
                    index + 1
                } else {
                    index
                };
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
        let index: usize = unescaped
            .parse()
            .with_context(|| format!("array index expected, got: {unescaped}"))?;
        if index >= arr.len() {
            bail!("array index out of bounds: {index}");
        }
        arr.remove(index);
    } else {
        bail!("parent is neither object nor array");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn synthesize_envelope(id: &str, version: u64, body: &str) -> Envelope {
        Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: id.to_string(),
            version,
            name: Name::Synthesize,
            operation: Operation {
                direction: "output".to_string(),
                format: Some("text/html".to_string()),
                encoding: None,
                content_encoding: None,
                token_budget: None,
                tokens_used: None,
                checksum: None,
                created_at: None,
                updated_at: None,
                state: None,
                state_changed_at: None,
            },
            content: vec![serde_json::json!({ "body": body })],
        }
    }

    fn id_target(id: &str) -> Target {
        Target::Id(id.to_string())
    }

    fn pointer_target(p: &str) -> Target {
        Target::Pointer(p.to_string())
    }

    #[test]
    fn test_apply_synthesize() {
        let op = synthesize_envelope("test", 1, "<div>hello</div>");
        let (result, handle) = apply(None, &op).unwrap();
        assert_eq!(result.name, Name::Synthesize);
        assert_eq!(extract_synthesize_item(&result).unwrap().body, "<div>hello</div>");
        assert_eq!(handle.name, Name::Handle);
    }

    #[test]
    fn test_apply_synthesize_with_targets() {
        let body = r#"<aap:target id="nav">menu</aap:target><aap:target id="stats">data</aap:target>"#;
        let op = synthesize_envelope("test", 1, body);
        let (_, handle) = apply(None, &op).unwrap();
        let handle_item: HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        assert_eq!(handle_item.sections, vec!["nav", "stats"]);
        assert!(handle_item.token_count.is_some());
    }

    #[test]
    fn test_edit_replace_by_id() {
        let body = r#"<aap:target id="revenue">$12,340</aap:target>"#;
        let artifact = synthesize_envelope("test", 1, body);
        let op = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "test".to_string(),
            version: 2,
            name: Name::Edit,
            operation: artifact.operation.clone(),
            content: vec![serde_json::to_value(DiffOp {
                op: OpType::Replace,
                target: id_target("revenue"),
                content: Some("$15,720".to_string()),
            })
            .unwrap()],
        };
        let (result, handle) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        assert!(out.contains("$15,720"));
        assert!(!out.contains("$12,340"));
        assert!(out.contains(r#"<aap:target id="revenue">"#));
        assert_eq!(handle.name, Name::Handle);
    }

    #[test]
    fn test_edit_delete_by_id() {
        let body = r#"before<aap:target id="tmp">remove</aap:target>after"#;
        let artifact = synthesize_envelope("test", 1, body);
        let op = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "test".to_string(),
            version: 2,
            name: Name::Edit,
            operation: artifact.operation.clone(),
            content: vec![serde_json::to_value(DiffOp {
                op: OpType::Delete,
                target: id_target("tmp"),
                content: None,
            })
            .unwrap()],
        };
        let (result, _) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        assert_eq!(out, r#"before<aap:target id="tmp"></aap:target>after"#);
    }

    #[test]
    fn test_edit_insert_after_by_id() {
        let body = r#"<aap:target id="list">item1</aap:target>"#;
        let artifact = synthesize_envelope("test", 1, body);
        let op = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "test".to_string(),
            version: 2,
            name: Name::Edit,
            operation: artifact.operation.clone(),
            content: vec![serde_json::to_value(DiffOp {
                op: OpType::InsertAfter,
                target: id_target("list"),
                content: Some(", item2".to_string()),
            })
            .unwrap()],
        };
        let (result, _) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        assert!(out.contains("item1, item2"));
    }

    #[test]
    fn test_nested_targets() {
        let body = r#"<aap:target id="outer"><h2>Stats</h2><aap:target id="val">100</aap:target></aap:target>"#;
        let artifact = synthesize_envelope("test", 1, body);
        let op = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "test".to_string(),
            version: 2,
            name: Name::Edit,
            operation: artifact.operation.clone(),
            content: vec![serde_json::to_value(DiffOp {
                op: OpType::Replace,
                target: id_target("val"),
                content: Some("200".to_string()),
            })
            .unwrap()],
        };
        let (result, handle) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        assert!(out.contains("200"));
        assert!(out.contains("<h2>Stats</h2>"));
        assert!(out.contains(r#"<aap:target id="outer">"#));
        // Handle should list both targets
        let handle_item: HandleContentItem =
            serde_json::from_value(handle.content[0].clone()).unwrap();
        assert!(handle_item.sections.contains(&"outer".to_string()));
        assert!(handle_item.sections.contains(&"val".to_string()));
    }

    #[test]
    fn test_targets_preserved_through_edit() {
        let body = r#"<aap:target id="x">old</aap:target>"#;
        let mut artifact = synthesize_envelope("test", 1, body);
        artifact.content = vec![serde_json::json!({
            "body": body,
            "targets": [{"id": "x", "label": "Test"}]
        })];
        let op = Envelope {
            protocol: PROTOCOL_VERSION.to_string(),
            id: "test".to_string(),
            version: 2,
            name: Name::Edit,
            operation: artifact.operation.clone(),
            content: vec![serde_json::to_value(DiffOp {
                op: OpType::Replace,
                target: id_target("x"),
                content: Some("new".to_string()),
            })
            .unwrap()],
        };
        let (result, _) = apply(Some(&artifact), &op).unwrap();
        let item = extract_synthesize_item(&result).unwrap();
        assert!(item.body.contains("new"));
        assert_eq!(item.targets.unwrap()[0].id, "x");
    }

    #[test]
    fn test_pointer_replace() {
        let base = r#"{"name": "Alice", "age": 30}"#;
        let artifact = synthesize_envelope("test", 1, base);
        let mut op = synthesize_envelope("test", 2, "");
        op.name = Name::Edit;
        op.operation.format = Some("application/json".to_string());
        op.content = vec![serde_json::to_value(DiffOp {
            op: OpType::Replace,
            target: pointer_target("/name"),
            content: Some(r#""Bob""#.to_string()),
        })
        .unwrap()];
        let (result, _) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        let parsed: serde_json::Value = serde_json::from_str(&out).unwrap();
        assert_eq!(parsed["name"], "Bob");
        assert_eq!(parsed["age"], 30);
    }

    #[test]
    fn test_pointer_delete() {
        let base = r#"{"name": "Alice", "temp": true}"#;
        let artifact = synthesize_envelope("test", 1, base);
        let mut op = synthesize_envelope("test", 2, "");
        op.name = Name::Edit;
        op.operation.format = Some("application/json".to_string());
        op.content = vec![serde_json::to_value(DiffOp {
            op: OpType::Delete,
            target: pointer_target("/temp"),
            content: None,
        })
        .unwrap()];
        let (result, _) = apply(Some(&artifact), &op).unwrap();
        let out = extract_synthesize_item(&result).unwrap().body;
        let parsed: serde_json::Value = serde_json::from_str(&out).unwrap();
        assert!(parsed.get("temp").is_none());
    }

    #[test]
    fn test_target_serde_roundtrip() {
        let t = Target::Id("revenue".to_string());
        let json = serde_json::to_string(&t).unwrap();
        let parsed: Target = serde_json::from_str(&json).unwrap();
        assert!(matches!(parsed, Target::Id(ref s) if s == "revenue"));

        let op = DiffOp {
            op: OpType::Replace,
            target: Target::Id("rev".to_string()),
            content: Some("new".to_string()),
        };
        let json = serde_json::to_string(&op).unwrap();
        let parsed: DiffOp = serde_json::from_str(&json).unwrap();
        assert!(matches!(parsed.target, Target::Id(ref s) if s == "rev"));
    }

    #[test]
    fn test_edit_from_json_string() {
        let json = r#"{
            "protocol": "aap/0.1", "id": "x", "version": 2, "name": "edit",
            "operation": {"direction": "output", "format": "text/html"},
            "content": [{"op": "replace", "target": {"type": "id", "value": "rev"}, "content": "new"}]
        }"#;
        let env: Envelope = serde_json::from_str(json).unwrap();
        let ops: Vec<DiffOp> = env.content.iter()
            .map(|v| serde_json::from_value(v.clone()).unwrap())
            .collect();
        assert!(matches!(ops[0].target, Target::Id(ref s) if s == "rev"));

        let art_json = r#"{"protocol":"aap/0.1","id":"x","version":1,"name":"synthesize","operation":{"direction":"output","format":"text/html"},"content":[{"body":"<aap:target id=\"rev\">old</aap:target>"}]}"#;
        let art: Envelope = serde_json::from_str(art_json).unwrap();
        let (result, _) = apply(Some(&art), &env).unwrap();
        let body = extract_synthesize_item(&result).unwrap().body;
        assert!(body.contains("new"));
        assert!(!body.contains("old"));
    }

    #[test]
    fn test_extract_target_ids() {
        let content = r#"<aap:target id="nav">menu</aap:target> <aap:target id="stats">data</aap:target>"#;
        let ids = extract_target_ids(content);
        assert_eq!(ids, vec!["nav", "stats"]);
    }

    #[test]
    fn test_extract_target_ids_empty() {
        let ids = extract_target_ids("no markers here");
        assert!(ids.is_empty());
    }
}
