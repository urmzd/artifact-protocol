//! Universal XML marker resolution for `<gap:target>`.
//!
//! All formats use `<gap:target id="...">` / `</gap:target>` markers.
//! The `gap:` namespace prefix is uniquely identifiable and LLMs follow XML tags
//! reliably. JSON uses pointer addressing instead.

use anyhow::{bail, Context, Result};
use regex::Regex;

/// Build start and end markers for a target ID.
///
/// `<gap:target id="nav">` / `</gap:target>`
///
/// JSON (`application/json`) does not support text markers — use pointer addressing.
pub fn markers_for(target_id: &str, format: &str) -> Result<(String, String)> {
    if format == "application/json" {
        bail!("JSON does not support text-based markers; use pointer addressing instead");
    }
    Ok((
        format!(r#"<gap:target id="{target_id}">"#),
        "</gap:target>".to_string(),
    ))
}

const OPEN_PREFIX: &str = "<gap:target ";
const CLOSE_TAG: &str = "</gap:target>";

/// Find the position of the matching `</gap:target>` for a target whose
/// opening tag ends at `content_start`. Tracks nesting depth so that inner
/// `<gap:target …>…</gap:target>` pairs are skipped.
fn find_matching_close(content: &str, content_start: usize) -> Option<usize> {
    let mut depth: usize = 1;
    let mut cursor = content_start;

    while cursor < content.len() && depth > 0 {
        // Find the next interesting tag (whichever comes first).
        let next_open = content[cursor..].find(OPEN_PREFIX).map(|i| cursor + i);
        let next_close = content[cursor..].find(CLOSE_TAG).map(|i| cursor + i);

        match (next_open, next_close) {
            (Some(o), Some(c)) if o < c => {
                depth += 1;
                cursor = o + OPEN_PREFIX.len();
            }
            (_, Some(c)) => {
                depth -= 1;
                if depth == 0 {
                    return Some(c);
                }
                cursor = c + CLOSE_TAG.len();
            }
            _ => break,
        }
    }
    None
}

/// Find the byte range of a target's content within a string.
///
/// Returns `(content_start, content_end)` — byte offsets between markers (exclusive of markers).
/// Handles nested `<gap:target>` elements via depth counting.
pub fn find_target_range(
    content: &str,
    target_id: &str,
    format: &str,
) -> Result<(usize, usize)> {
    let (start_marker, _) = markers_for(target_id, format)?;
    let si = content
        .find(&start_marker)
        .with_context(|| format!("start marker not found for target: {target_id}"))?;
    let content_start = si + start_marker.len();
    let ei = find_matching_close(content, content_start)
        .with_context(|| format!("end marker not found for target: {target_id}"))?;
    Ok((content_start, ei))
}

/// Find the byte range of a target including its markers.
///
/// Returns `(marker_start, marker_end)` — byte offsets including both markers and content.
/// Handles nested `<gap:target>` elements via depth counting.
pub fn find_target_range_inclusive(
    content: &str,
    target_id: &str,
    format: &str,
) -> Result<(usize, usize)> {
    let (start_marker, _) = markers_for(target_id, format)?;
    let si = content
        .find(&start_marker)
        .with_context(|| format!("start marker not found for target: {target_id}"))?;
    let content_start = si + start_marker.len();
    let ei = find_matching_close(content, content_start)
        .with_context(|| format!("end marker not found for target: {target_id}"))?;
    Ok((si, ei + CLOSE_TAG.len()))
}

/// Extract all target IDs from artifact content by scanning for `<gap:target id="...">` markers.
///
/// Returns IDs in document order. JSON format returns an empty vec (uses pointer addressing).
pub fn extract_targets(content: &str, format: &str) -> Vec<String> {
    if format == "application/json" {
        return Vec::new();
    }
    let re = Regex::new(r#"<gap:target id="([^"]+)">"#).expect("valid regex");
    re.captures_iter(content)
        .map(|cap| cap[1].to_string())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_html_markers() {
        let (start, end) = markers_for("nav", "text/html").unwrap();
        assert_eq!(start, r#"<gap:target id="nav">"#);
        assert_eq!(end, "</gap:target>");
    }

    #[test]
    fn test_python_markers() {
        let (start, end) = markers_for("imports", "text/x-python").unwrap();
        assert_eq!(start, r#"<gap:target id="imports">"#);
        assert_eq!(end, "</gap:target>");
    }

    #[test]
    fn test_json_unsupported() {
        assert!(markers_for("data", "application/json").is_err());
    }

    #[test]
    fn test_find_target_range() {
        let content = r#"before<gap:target id="stats">old stats</gap:target>after"#;
        let (start, end) = find_target_range(content, "stats", "text/html").unwrap();
        assert_eq!(&content[start..end], "old stats");
    }

    #[test]
    fn test_find_target_range_nested_inner() {
        let content = r#"<gap:target id="outer"><gap:target id="inner">val</gap:target></gap:target>"#;
        let (start, end) = find_target_range(content, "inner", "text/html").unwrap();
        assert_eq!(&content[start..end], "val");
    }

    #[test]
    fn test_find_target_range_nested_outer() {
        let content = r#"<gap:target id="outer"><gap:target id="inner">val</gap:target></gap:target>"#;
        let (start, end) = find_target_range(content, "outer", "text/html").unwrap();
        assert_eq!(&content[start..end], r#"<gap:target id="inner">val</gap:target>"#);
    }

    #[test]
    fn test_find_target_range_inclusive() {
        let content = r#"before<gap:target id="x">data</gap:target>after"#;
        let (start, end) = find_target_range_inclusive(content, "x", "text/html").unwrap();
        assert_eq!(&content[start..end], r#"<gap:target id="x">data</gap:target>"#);
    }

    #[test]
    fn test_extract_targets_flat() {
        let content = r#"<gap:target id="a">x</gap:target><gap:target id="b">y</gap:target>"#;
        assert_eq!(extract_targets(content, "text/html"), vec!["a", "b"]);
    }

    #[test]
    fn test_extract_targets_nested() {
        let content = r#"<gap:target id="outer"><gap:target id="inner">v</gap:target></gap:target>"#;
        assert_eq!(extract_targets(content, "text/html"), vec!["outer", "inner"]);
    }

    #[test]
    fn test_extract_targets_empty() {
        assert!(extract_targets("no markers here", "text/html").is_empty());
    }

    #[test]
    fn test_extract_targets_json_returns_empty() {
        let content = r#"<gap:target id="a">x</gap:target>"#;
        assert!(extract_targets(content, "application/json").is_empty());
    }
}
