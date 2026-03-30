//! Generates the benchmark comparison table as Markdown.
//!
//! Usage: cargo run --bin bench-table > benches/results.md

use std::collections::HashMap;

use artifact_generator::apply::{
    apply_diff, apply_section_update, assemble_manifest, fill_template,
};
use artifact_generator::aap::{DiffOp, OpType, SectionUpdate, Target};

const FULL_HTML: &str = include_str!("../../benches/protocol_fixture.html");

fn main() {
    let full_size = FULL_HTML.len();

    // ── Build payloads ──────────────────────────────────────────────────────

    let diff_1 = vec![DiffOp {
        op: OpType::Replace,
        target: Target {
            search: Some("24,891".into()),
            lines: None,
            offsets: None,
            section: None,
        },
        content: Some("27,103".into()),
    }];

    let diff_4 = vec![
        DiffOp {
            op: OpType::Replace,
            target: Target { search: Some("24,891".into()), lines: None, offsets: None, section: None },
            content: Some("31,205".into()),
        },
        DiffOp {
            op: OpType::Replace,
            target: Target { search: Some("$182,430".into()), lines: None, offsets: None, section: None },
            content: Some("$210,880".into()),
        },
        DiffOp {
            op: OpType::Replace,
            target: Target { search: Some("3,047".into()), lines: None, offsets: None, section: None },
            content: Some("4,112".into()),
        },
        DiffOp {
            op: OpType::Replace,
            target: Target { search: Some("99.97%".into()), lines: None, offsets: None, section: None },
            content: Some("99.99%".into()),
        },
    ];

    let section_1 = vec![SectionUpdate {
        id: "stats".into(),
        content: r#"<div class="stats">
  <div class="card"><div class="card-label">Total Users</div><div class="card-value">31,205</div></div>
  <div class="card"><div class="card-label">Revenue (MTD)</div><div class="card-value">$210,880</div></div>
  <div class="card"><div class="card-label">Orders (MTD)</div><div class="card-value">4,112</div></div>
  <div class="card"><div class="card-label">Uptime</div><div class="card-value">99.99%</div></div>
</div>"#
            .into(),
    }];

    let section_2 = vec![
        SectionUpdate {
            id: "stats".into(),
            content: r#"<div class="stats">
  <div class="card"><div class="card-label">Total Users</div><div class="card-value">31,205</div></div>
  <div class="card"><div class="card-label">Revenue (MTD)</div><div class="card-value">$210,880</div></div>
</div>"#
                .into(),
        },
        SectionUpdate {
            id: "orders".into(),
            content: r#"<div class="section">
  <div class="section-header"><span class="section-title">Recent Orders</span></div>
  <table><thead><tr><th>ID</th><th>Product</th><th>Amount</th></tr></thead>
  <tbody><tr><td>ORD-200001</td><td>New Product</td><td>$99.99</td></tr></tbody></table>
</div>"#
                .into(),
        },
    ];

    let template = r#"<!DOCTYPE html>
<html><head><title>{{title}}</title></head>
<body>
<h1>{{title}}</h1>
<div class="stats">
  <div>Users: {{users}}</div>
  <div>Revenue: {{revenue}}</div>
  <div>Orders: {{orders}}</div>
</div>
{{{users_table}}}
{{{orders_table}}}
</body></html>"#;

    let mut bindings = HashMap::new();
    bindings.insert("title".into(), serde_json::Value::String("Dashboard".into()));
    bindings.insert("brand".into(), serde_json::Value::String("AcmeCorp".into()));
    bindings.insert("users".into(), serde_json::Value::String("31,205".into()));
    bindings.insert("revenue".into(), serde_json::Value::String("$210,880".into()));
    bindings.insert("orders".into(), serde_json::Value::String("4,112".into()));
    bindings.insert("uptime".into(), serde_json::Value::String("99.99%".into()));
    bindings.insert(
        "users_table".into(),
        serde_json::Value::String("<table><tr><td>Alice</td></tr><tr><td>Bob</td></tr></table>".into()),
    );
    bindings.insert(
        "orders_table".into(),
        serde_json::Value::String("<table><tr><td>ORD-001</td></tr></table>".into()),
    );

    let manifest_skeleton = r#"<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>body{font-family:system-ui}</style></head>
<body>
<!-- section:nav --><!-- /section:nav -->
<main>
<!-- section:stats --><!-- /section:stats -->
<!-- section:users --><!-- /section:users -->
<!-- section:orders --><!-- /section:orders -->
</main>
</body></html>"#;

    let mut manifest_sections: HashMap<String, String> = HashMap::new();
    manifest_sections.insert(
        "nav".into(),
        r##"<nav><span>AcmeCorp</span></nav>
<aside><a href="#">Dashboard</a><a href="#">Analytics</a></aside>"##
            .into(),
    );
    manifest_sections.insert(
        "stats".into(),
        r#"<div class="stats">
  <div class="card"><span>Users: 31,205</span></div>
  <div class="card"><span>Revenue: $210,880</span></div>
</div>"#
            .into(),
    );
    manifest_sections.insert(
        "users".into(),
        r#"<table>
  <tr><th>Name</th><th>Email</th></tr>
  <tr><td>Alice</td><td>alice@example.com</td></tr>
  <tr><td>Bob</td><td>bob@example.com</td></tr>
</table>"#
            .into(),
    );
    manifest_sections.insert(
        "orders".into(),
        r#"<table>
  <tr><th>ID</th><th>Product</th></tr>
  <tr><td>ORD-001</td><td>Widget</td></tr>
</table>"#
            .into(),
    );

    // ── Compute sizes ───────────────────────────────────────────────────────

    let diff_1_bytes: usize = diff_1.iter().map(|op| {
        op.target.search.as_ref().map_or(0, |s| s.len()) + op.content.as_ref().map_or(0, |s| s.len())
    }).sum();
    let diff_4_bytes: usize = diff_4.iter().map(|op| {
        op.target.search.as_ref().map_or(0, |s| s.len()) + op.content.as_ref().map_or(0, |s| s.len())
    }).sum();
    let section_1_bytes: usize = section_1.iter().map(|u| u.content.len()).sum();
    let section_2_bytes: usize = section_2.iter().map(|u| u.content.len()).sum();
    let template_bytes: usize = bindings.values().map(|v| match v {
        serde_json::Value::String(s) => s.len(),
        _ => 0,
    }).sum();
    let manifest_bytes: usize = manifest_sections.values().map(|s| s.len()).sum();

    // ── Verify applies work ─────────────────────────────────────────────────

    apply_diff(FULL_HTML, &diff_1).expect("diff_1 failed");
    apply_diff(FULL_HTML, &diff_4).expect("diff_4 failed");
    apply_section_update(FULL_HTML, &section_1).expect("section_1 failed");
    apply_section_update(FULL_HTML, &section_2).expect("section_2 failed");
    fill_template(template, &bindings);
    assemble_manifest(manifest_skeleton, &manifest_sections).expect("manifest failed");

    // ── Timing ──────────────────────────────────────────────────────────────

    let iters = 10_000u64;

    let time_full = bench_ns(iters, || { let _ = FULL_HTML.to_string(); });
    let time_diff_1 = bench_ns(iters, || { let _ = apply_diff(FULL_HTML, &diff_1).unwrap(); });
    let time_diff_4 = bench_ns(iters, || { let _ = apply_diff(FULL_HTML, &diff_4).unwrap(); });
    let time_section_1 = bench_ns(iters, || { let _ = apply_section_update(FULL_HTML, &section_1).unwrap(); });
    let time_section_2 = bench_ns(iters, || { let _ = apply_section_update(FULL_HTML, &section_2).unwrap(); });
    let time_template = bench_ns(iters, || { let _ = fill_template(template, &bindings); });
    let time_manifest = bench_ns(iters, || { let _ = assemble_manifest(manifest_skeleton, &manifest_sections).unwrap(); });

    // ── Output Markdown ─────────────────────────────────────────────────────

    struct Row {
        mode: &'static str,
        scenario: &'static str,
        payload: usize,
        pct: f64,
        savings: f64,
        time_ns: u64,
    }

    let rows = vec![
        Row { mode: "full", scenario: "Full regeneration (baseline)", payload: full_size, pct: 100.0, savings: 0.0, time_ns: time_full },
        Row { mode: "diff", scenario: "1 value change", payload: diff_1_bytes, pct: diff_1_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - diff_1_bytes as f64 / full_size as f64) * 100.0, time_ns: time_diff_1 },
        Row { mode: "diff", scenario: "4 value changes", payload: diff_4_bytes, pct: diff_4_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - diff_4_bytes as f64 / full_size as f64) * 100.0, time_ns: time_diff_4 },
        Row { mode: "section", scenario: "1 section replaced", payload: section_1_bytes, pct: section_1_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - section_1_bytes as f64 / full_size as f64) * 100.0, time_ns: time_section_1 },
        Row { mode: "section", scenario: "2 sections replaced", payload: section_2_bytes, pct: section_2_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - section_2_bytes as f64 / full_size as f64) * 100.0, time_ns: time_section_2 },
        Row { mode: "template", scenario: "8 slot bindings", payload: template_bytes, pct: template_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - template_bytes as f64 / full_size as f64) * 100.0, time_ns: time_template },
        Row { mode: "manifest", scenario: "4 sections assembled", payload: manifest_bytes, pct: manifest_bytes as f64 / full_size as f64 * 100.0, savings: (1.0 - manifest_bytes as f64 / full_size as f64) * 100.0, time_ns: time_manifest },
    ];

    println!("| Mode | Scenario | Payload | % of Full | Savings | Apply Time |");
    println!("|---|---|---:|---:|---:|---:|");
    for r in &rows {
        let time_str = if r.time_ns >= 1_000 {
            format!("{:.1} \u{00b5}s", r.time_ns as f64 / 1_000.0)
        } else {
            format!("{} ns", r.time_ns)
        };
        let payload_str = fmt_thousands(r.payload);
        if r.mode == "full" {
            println!(
                "| **{}** | {} | {} B | {:.1}% | — | {} |",
                r.mode, r.scenario, payload_str, r.pct, time_str,
            );
        } else {
            println!(
                "| **{}** | {} | {} B | {:.1}% | **{:.1}%** | {} |",
                r.mode, r.scenario, payload_str, r.pct, r.savings, time_str,
            );
        }
    }
}

fn fmt_thousands(n: usize) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result.chars().rev().collect()
}

fn bench_ns<F: FnMut()>(iters: u64, mut f: F) -> u64 {
    // Warmup
    for _ in 0..100 {
        f();
    }
    let start = std::time::Instant::now();
    for _ in 0..iters {
        f();
    }
    let elapsed = start.elapsed();
    elapsed.as_nanos() as u64 / iters
}
