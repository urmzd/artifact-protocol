//! Artifact resolution — applies diff, section, template, and composite modes
//! to produce final artifact content.

use anyhow::{bail, Context, Result};
use std::collections::HashMap;

use crate::aap::{DiffOp, Envelope, Include, Mode, OpType, SectionUpdate};

/// Resolve an envelope to its final content string.
///
/// For `full` mode, returns content directly.
/// For other modes, requires the base content from the store.
pub fn resolve(envelope: &Envelope, store: &HashMap<String, String>) -> Result<String> {
    match envelope.mode {
        Mode::Full => envelope
            .content
            .clone()
            .context("full-mode envelope missing content"),
        Mode::Diff => {
            let base = store
                .get(&envelope.id)
                .context("no base content for diff")?;
            let ops = envelope
                .operations
                .as_ref()
                .context("diff-mode envelope missing operations")?;
            apply_diff(base, ops)
        }
        Mode::Section => {
            let base = store
                .get(&envelope.id)
                .context("no base content for section update")?;
            let updates = envelope
                .target_sections
                .as_ref()
                .context("section-mode envelope missing target_sections")?;
            apply_section_update(base, updates)
        }
        Mode::Template => {
            let template = envelope
                .template
                .as_ref()
                .context("template-mode envelope missing template")?;
            let bindings = envelope
                .bindings
                .as_ref()
                .context("template-mode envelope missing bindings")?;
            Ok(fill_template(template, bindings))
        }
        Mode::Composite => {
            let includes = envelope
                .includes
                .as_ref()
                .context("composite-mode envelope missing includes")?;
            resolve_composite(includes, store)
        }
        Mode::Manifest => {
            // Manifest mode is an orchestration concern — the consumer cannot
            // resolve it directly. It must be processed by an orchestrator that
            // dispatches section generations and assembles results.
            // If we receive a manifest with section results already assembled
            // in the skeleton, we can assemble them.
            let skeleton = envelope
                .skeleton
                .as_ref()
                .context("manifest-mode envelope missing skeleton")?;
            Ok(skeleton.clone())
        }
    }
}

/// Apply diff operations sequentially to base content.
pub fn apply_diff(base: &str, operations: &[DiffOp]) -> Result<String> {
    let mut result = base.to_string();

    for (i, op) in operations.iter().enumerate() {
        let (start, end) = find_target_range(&result, &op.target)
            .with_context(|| format!("operation {i}: target not found"))?;

        match op.op {
            OpType::Replace => {
                let content = op.content.as_deref().unwrap_or("");
                result = format!("{}{}{}", &result[..start], content, &result[end..]);
            }
            OpType::Delete => {
                result = format!("{}{}", &result[..start], &result[end..]);
            }
            OpType::InsertBefore => {
                let content = op.content.as_deref().unwrap_or("");
                result = format!("{}{}{}", &result[..start], content, &result[start..]);
            }
            OpType::InsertAfter => {
                let content = op.content.as_deref().unwrap_or("");
                result = format!("{}{}{}", &result[..end], content, &result[end..]);
            }
        }
    }

    Ok(result)
}

/// Replace section content, preserving markers and other sections.
pub fn apply_section_update(base: &str, updates: &[SectionUpdate]) -> Result<String> {
    let mut result = base.to_string();

    for update in updates {
        let start_marker = format!("<!-- section:{} -->", update.id);
        let end_marker = format!("<!-- /section:{} -->", update.id);

        let si = result
            .find(&start_marker)
            .with_context(|| format!("start marker not found for section: {}", update.id))?;
        let ei = result
            .find(&end_marker)
            .with_context(|| format!("end marker not found for section: {}", update.id))?;

        let before = &result[..si + start_marker.len()];
        let after = &result[ei..];
        result = format!("{}\n{}\n{}", before, update.content, after);
    }

    Ok(result)
}

/// Simple Mustache-subset template filling (variable substitution).
pub fn fill_template(template: &str, bindings: &HashMap<String, serde_json::Value>) -> String {
    let mut result = template.to_string();
    for (key, value) in bindings {
        let val_str = match value {
            serde_json::Value::String(s) => s.clone(),
            other => other.to_string(),
        };
        // Unescaped triple-brace
        result = result.replace(&format!("{{{{{{{key}}}}}}}"), &val_str);
        // Regular double-brace
        result = result.replace(&format!("{{{{{key}}}}}"), &val_str);
    }
    result
}

/// Assemble content from include references.
pub fn resolve_composite(
    includes: &[Include],
    store: &HashMap<String, String>,
) -> Result<String> {
    let mut parts = Vec::new();

    for inc in includes {
        if let Some(content) = &inc.content {
            parts.push(content.clone());
        } else if let Some(reference) = &inc.reference {
            if let Some((artifact_id, section_id)) = reference.split_once(':') {
                let content = store
                    .get(artifact_id)
                    .with_context(|| format!("referenced artifact not found: {artifact_id}"))?;
                let start_marker = format!("<!-- section:{section_id} -->");
                let end_marker = format!("<!-- /section:{section_id} -->");
                let si = content
                    .find(&start_marker)
                    .with_context(|| format!("section not found: {section_id}"))?;
                let ei = content
                    .find(&end_marker)
                    .with_context(|| format!("end marker not found: {section_id}"))?;
                parts.push(content[si..ei + end_marker.len()].to_string());
            } else {
                let content = store
                    .get(reference.as_str())
                    .with_context(|| format!("referenced artifact not found: {reference}"))?;
                parts.push(content.clone());
            }
        } else if let Some(uri) = &inc.uri {
            parts.push(format!("<!-- unresolved: {uri} -->"));
        } else {
            bail!("include has no ref, uri, or content");
        }
    }

    Ok(parts.join("\n"))
}

/// Assemble a manifest by stitching section results into the skeleton.
///
/// Each entry in `section_results` maps a section ID to its generated content.
/// The content is inserted between the corresponding section markers in the skeleton.
pub fn assemble_manifest(
    skeleton: &str,
    section_results: &HashMap<String, String>,
) -> Result<String> {
    let mut result = skeleton.to_string();
    for (section_id, content) in section_results {
        let start_marker = format!("<!-- section:{section_id} -->");
        let end_marker = format!("<!-- /section:{section_id} -->");
        let si = result
            .find(&start_marker)
            .with_context(|| format!("section marker not found in skeleton: {section_id}"))?;
        let ei = result
            .find(&end_marker)
            .with_context(|| format!("end marker not found in skeleton: {section_id}"))?;
        let before = &result[..si + start_marker.len()];
        let after = &result[ei..];
        result = format!("{before}\n{content}\n{after}");
    }
    Ok(result)
}

/// Find the byte range targeted by a diff operation's target.
fn find_target_range(
    content: &str,
    target: &crate::aap::Target,
) -> Result<(usize, usize)> {
    if let Some(search) = &target.search {
        let idx = content
            .find(search.as_str())
            .with_context(|| format!("search target not found: {search:?}"))?;
        Ok((idx, idx + search.len()))
    } else if let Some(offsets) = &target.offsets {
        Ok((offsets[0] as usize, offsets[1] as usize))
    } else if let Some(lines) = &target.lines {
        let content_lines: Vec<&str> = content.split('\n').collect();
        let start_line = (lines[0] as usize).saturating_sub(1);
        let end_line = lines[1] as usize;
        let start = content_lines[..start_line]
            .iter()
            .map(|l| l.len() + 1)
            .sum::<usize>();
        let end = content_lines[..end_line]
            .iter()
            .map(|l| l.len() + 1)
            .sum::<usize>()
            .saturating_sub(1);
        Ok((start, end))
    } else if let Some(section) = &target.section {
        let start_marker = format!("<!-- section:{section} -->");
        let end_marker = format!("<!-- /section:{section} -->");
        let si = content
            .find(&start_marker)
            .with_context(|| format!("section start not found: {section}"))?;
        let ei = content
            .find(&end_marker)
            .with_context(|| format!("section end not found: {section}"))?;
        Ok((si + start_marker.len(), ei))
    } else {
        bail!("target has no addressing mode")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aap::{DiffOp, OpType, Target};

    #[test]
    fn test_apply_diff_search_replace() {
        let base = "<div>old value</div>";
        let ops = vec![DiffOp {
            op: OpType::Replace,
            target: Target {
                search: Some("old value".to_string()),
                lines: None,
                offsets: None,
                section: None,
            },
            content: Some("new value".to_string()),
        }];
        let result = apply_diff(base, &ops).unwrap();
        assert_eq!(result, "<div>new value</div>");
    }

    #[test]
    fn test_apply_diff_delete() {
        let base = "keep this, remove this, keep that";
        let ops = vec![DiffOp {
            op: OpType::Delete,
            target: Target {
                search: Some(", remove this".to_string()),
                lines: None,
                offsets: None,
                section: None,
            },
            content: None,
        }];
        let result = apply_diff(base, &ops).unwrap();
        assert_eq!(result, "keep this, keep that");
    }

    #[test]
    fn test_apply_section_update() {
        let base = "before\n<!-- section:stats -->\nold stats\n<!-- /section:stats -->\nafter";
        let updates = vec![SectionUpdate {
            id: "stats".to_string(),
            content: "new stats".to_string(),
        }];
        let result = apply_section_update(base, &updates).unwrap();
        assert!(result.contains("new stats"));
        assert!(result.contains("before"));
        assert!(result.contains("after"));
    }

    #[test]
    fn test_fill_template() {
        let template = "<h1>{{title}}</h1><p>{{{body}}}</p>";
        let mut bindings = HashMap::new();
        bindings.insert(
            "title".to_string(),
            serde_json::Value::String("Hello".to_string()),
        );
        bindings.insert(
            "body".to_string(),
            serde_json::Value::String("<b>World</b>".to_string()),
        );
        let result = fill_template(template, &bindings);
        assert_eq!(result, "<h1>Hello</h1><p><b>World</b></p>");
    }

    #[test]
    fn test_assemble_manifest() {
        let skeleton =
            "<html><!-- section:nav --><!-- /section:nav --><main><!-- section:body --><!-- /section:body --></main></html>";
        let mut sections = HashMap::new();
        sections.insert("nav".to_string(), "<nav>Home</nav>".to_string());
        sections.insert("body".to_string(), "<h1>Hello</h1>".to_string());
        let result = assemble_manifest(skeleton, &sections).unwrap();
        assert!(result.contains("<nav>Home</nav>"));
        assert!(result.contains("<h1>Hello</h1>"));
        assert!(result.contains("<!-- section:nav -->"));
        assert!(result.contains("<!-- /section:body -->"));
    }
}
