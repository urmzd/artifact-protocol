//! Agent-Artifact Protocol (AAP) benchmarks — measures apply time and payload size
//! for each generation mode against the full-regeneration baseline.
//!
//! Run: cargo bench --bench aap

use std::collections::HashMap;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

use artifact_generator::apply::{
    apply_diff, apply_section_update, assemble_manifest, fill_template,
};
use artifact_generator::aap::{DiffOp, OpType, SectionUpdate, Target};

const FULL_HTML: &str = include_str!("protocol_fixture.html");

// ── Payloads ────────────────────────────────────────────────────────────────

fn single_diff_ops() -> Vec<DiffOp> {
    vec![DiffOp {
        op: OpType::Replace,
        target: Target {
            search: Some("24,891".into()),
            lines: None,
            offsets: None,
            section: None,
        },
        content: Some("27,103".into()),
    }]
}

fn multi_diff_ops() -> Vec<DiffOp> {
    vec![
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
    ]
}

fn stats_section_update() -> Vec<SectionUpdate> {
    vec![SectionUpdate {
        id: "stats".into(),
        content: r#"<div class="stats">
  <div class="card"><div class="card-label">Total Users</div><div class="card-value">31,205</div></div>
  <div class="card"><div class="card-label">Revenue (MTD)</div><div class="card-value">$210,880</div></div>
  <div class="card"><div class="card-label">Orders (MTD)</div><div class="card-value">4,112</div></div>
  <div class="card"><div class="card-label">Uptime</div><div class="card-value">99.99%</div></div>
</div>"#.into(),
    }]
}

fn multi_section_update() -> Vec<SectionUpdate> {
    vec![
        SectionUpdate {
            id: "stats".into(),
            content: r#"<div class="stats">
  <div class="card"><div class="card-label">Total Users</div><div class="card-value">31,205</div></div>
  <div class="card"><div class="card-label">Revenue (MTD)</div><div class="card-value">$210,880</div></div>
</div>"#.into(),
        },
        SectionUpdate {
            id: "orders".into(),
            content: r#"<div class="section">
  <div class="section-header"><span class="section-title">Recent Orders</span></div>
  <table><thead><tr><th>ID</th><th>Product</th><th>Amount</th></tr></thead>
  <tbody><tr><td>ORD-200001</td><td>New Product</td><td>$99.99</td></tr></tbody></table>
</div>"#.into(),
        },
    ]
}

fn template_and_bindings() -> (String, HashMap<String, serde_json::Value>) {
    let template = r#"<!DOCTYPE html>
<html><head><title>{{title}}</title></head>
<body>
<nav><span>{{brand}}</span></nav>
<div class="stats">
  <div class="card"><span>Users</span><span>{{users}}</span></div>
  <div class="card"><span>Revenue</span><span>{{revenue}}</span></div>
  <div class="card"><span>Orders</span><span>{{orders}}</span></div>
  <div class="card"><span>Uptime</span><span>{{uptime}}</span></div>
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
    bindings.insert("users_table".into(), serde_json::Value::String(
        "<table><tr><td>Alice</td></tr><tr><td>Bob</td></tr></table>".into()
    ));
    bindings.insert("orders_table".into(), serde_json::Value::String(
        "<table><tr><td>ORD-001</td></tr></table>".into()
    ));

    (template.into(), bindings)
}

fn manifest_skeleton_and_sections() -> (String, HashMap<String, String>) {
    let skeleton = r#"<!DOCTYPE html>
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

    let mut sections = HashMap::new();
    sections.insert("nav".into(), r##"<nav><span>AcmeCorp</span></nav>
<aside><a href="#">Dashboard</a><a href="#">Analytics</a></aside>"##.into());
    sections.insert("stats".into(), r#"<div class="stats">
  <div class="card"><span>Users: 31,205</span></div>
  <div class="card"><span>Revenue: $210,880</span></div>
</div>"#.into());
    sections.insert("users".into(), r#"<table>
  <tr><th>Name</th><th>Email</th></tr>
  <tr><td>Alice</td><td>alice@example.com</td></tr>
  <tr><td>Bob</td><td>bob@example.com</td></tr>
</table>"#.into());
    sections.insert("orders".into(), r#"<table>
  <tr><th>ID</th><th>Product</th></tr>
  <tr><td>ORD-001</td><td>Widget</td></tr>
</table>"#.into());

    (skeleton.into(), sections)
}

// ── Byte-size helper ────────────────────────────────────────────────────────

fn payload_bytes(ops: &[DiffOp]) -> usize {
    ops.iter().map(|op| {
        let search_len = op.target.search.as_ref().map_or(0, |s| s.len());
        let content_len = op.content.as_ref().map_or(0, |s| s.len());
        search_len + content_len
    }).sum()
}

fn section_payload_bytes(updates: &[SectionUpdate]) -> usize {
    updates.iter().map(|u| u.content.len()).sum()
}

// ── Benchmarks ──────────────────────────────────────────────────────────────

fn bench_baseline_full_copy(c: &mut Criterion) {
    // Baseline: simulate "full regeneration" cost = copying the entire artifact
    c.bench_function("baseline_full_copy", |b| {
        b.iter(|| {
            let copy = FULL_HTML.to_string();
            std::hint::black_box(copy);
        });
    });
}

fn bench_diff(c: &mut Criterion) {
    let mut group = c.benchmark_group("diff_apply");
    let single = single_diff_ops();
    let multi = multi_diff_ops();

    group.bench_with_input(
        BenchmarkId::new("single_replace", format!("{}B payload", payload_bytes(&single))),
        &single,
        |b, ops| b.iter(|| apply_diff(FULL_HTML, ops).unwrap()),
    );
    group.bench_with_input(
        BenchmarkId::new("four_replaces", format!("{}B payload", payload_bytes(&multi))),
        &multi,
        |b, ops| b.iter(|| apply_diff(FULL_HTML, ops).unwrap()),
    );
    group.finish();
}

fn bench_section(c: &mut Criterion) {
    let mut group = c.benchmark_group("section_apply");
    let single = stats_section_update();
    let multi = multi_section_update();

    group.bench_with_input(
        BenchmarkId::new("one_section", format!("{}B payload", section_payload_bytes(&single))),
        &single,
        |b, updates| b.iter(|| apply_section_update(FULL_HTML, updates).unwrap()),
    );
    group.bench_with_input(
        BenchmarkId::new("two_sections", format!("{}B payload", section_payload_bytes(&multi))),
        &multi,
        |b, updates| b.iter(|| apply_section_update(FULL_HTML, updates).unwrap()),
    );
    group.finish();
}

fn bench_template(c: &mut Criterion) {
    let (template, bindings) = template_and_bindings();
    let bindings_size: usize = bindings.values().map(|v| {
        match v { serde_json::Value::String(s) => s.len(), _ => 0 }
    }).sum();

    c.bench_function(
        &format!("template_fill/{}B bindings", bindings_size),
        |b| b.iter(|| fill_template(&template, &bindings)),
    );
}

fn bench_manifest_assembly(c: &mut Criterion) {
    let (skeleton, sections) = manifest_skeleton_and_sections();
    let total_section_bytes: usize = sections.values().map(|s| s.len()).sum();

    c.bench_function(
        &format!("manifest_assemble/4_sections_{}B", total_section_bytes),
        |b| b.iter(|| assemble_manifest(&skeleton, &sections).unwrap()),
    );
}

fn bench_payload_comparison(c: &mut Criterion) {
    // Print payload sizes for reference (runs once as a "benchmark")
    let full_size = FULL_HTML.len();
    let single_diff = payload_bytes(&single_diff_ops());
    let multi_diff = payload_bytes(&multi_diff_ops());
    let single_section = section_payload_bytes(&stats_section_update());
    let multi_section = section_payload_bytes(&multi_section_update());
    let (_, bindings) = template_and_bindings();
    let template_size: usize = bindings.values().map(|v| {
        match v { serde_json::Value::String(s) => s.len(), _ => 0 }
    }).sum();
    let (_, manifest_sections) = manifest_skeleton_and_sections();
    let manifest_size: usize = manifest_sections.values().map(|s| s.len()).sum();

    eprintln!();
    eprintln!("─── Payload Size Comparison ────────────────────────────────");
    eprintln!("  Full artifact:        {:>6} bytes (baseline)", full_size);
    eprintln!("  Diff (1 replace):     {:>6} bytes ({:.1}% of full)", single_diff, single_diff as f64 / full_size as f64 * 100.0);
    eprintln!("  Diff (4 replaces):    {:>6} bytes ({:.1}% of full)", multi_diff, multi_diff as f64 / full_size as f64 * 100.0);
    eprintln!("  Section (1 section):  {:>6} bytes ({:.1}% of full)", single_section, single_section as f64 / full_size as f64 * 100.0);
    eprintln!("  Section (2 sections): {:>6} bytes ({:.1}% of full)", multi_section, multi_section as f64 / full_size as f64 * 100.0);
    eprintln!("  Template (bindings):  {:>6} bytes ({:.1}% of full)", template_size, template_size as f64 / full_size as f64 * 100.0);
    eprintln!("  Manifest (4 sections):{:>6} bytes ({:.1}% of full)", manifest_size, manifest_size as f64 / full_size as f64 * 100.0);
    eprintln!("────────────────────────────────────────────────────────────");
    eprintln!();

    // Dummy bench so criterion doesn't complain
    c.bench_function("payload_sizes_printed", |b| b.iter(|| 1 + 1));
}

criterion_group!(
    benches,
    bench_payload_comparison,
    bench_baseline_full_copy,
    bench_diff,
    bench_section,
    bench_template,
    bench_manifest_assembly,
);
criterion_main!(benches);
