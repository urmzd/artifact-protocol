//! Agent-Artifact Protocol (AAP) benchmarks — measures apply time and payload size
//! using real fixtures from evals/data/apply-engine/.
//!
//! Run: cargo bench --bench aap

use std::fs;
use std::path::PathBuf;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

use aap::aap::{EditOp, Envelope};
use aap::apply::{apply_edit, TextResolver};

// ── Fixture loading ────────────────────────────────────────────────────────

struct Fixture {
    case: String,
    artifact: String,
    diff_replace_ops: Vec<Vec<EditOp>>,
    diff_multi_ops: Vec<Vec<EditOp>>,
    diff_delete_ops: Vec<Vec<EditOp>>,
}

fn fixtures_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("evals/data/apply-engine")
}

fn load_fixture(case_dir: &str) -> Fixture {
    let base = fixtures_dir().join(case_dir);
    let artifact = fs::read_to_string(base.join("artifacts/dashboard.html"))
        .expect("read artifact");

    let parse_envelopes = |name: &str| -> Vec<Envelope> {
        let path = base.join("envelopes").join(name);
        fs::read_to_string(&path)
            .unwrap_or_default()
            .lines()
            .filter(|l| !l.trim().is_empty())
            .map(|l| Envelope::from_json(l).expect("parse envelope"))
            .collect()
    };

    let parse_diff_ops = |envs: Vec<Envelope>| -> Vec<Vec<EditOp>> {
        envs.into_iter()
            .map(|env| {
                env.content
                    .into_iter()
                    .map(|v| serde_json::from_value::<EditOp>(v).expect("parse EditOp"))
                    .collect()
            })
            .collect()
    };

    Fixture {
        case: case_dir.into(),
        artifact,
        diff_replace_ops: parse_diff_ops(parse_envelopes("edit-replace.jsonl")),
        diff_multi_ops: parse_diff_ops(parse_envelopes("edit-multi.jsonl")),
        diff_delete_ops: parse_diff_ops(parse_envelopes("edit-delete.jsonl")),
    }
}

fn all_fixtures() -> Vec<Fixture> {
    let dir = fixtures_dir();
    let mut cases: Vec<String> = fs::read_dir(&dir)
        .expect("read apply-engine dir")
        .filter_map(|e| {
            let e = e.ok()?;
            if e.file_type().ok()?.is_dir() {
                Some(e.file_name().to_string_lossy().to_string())
            } else {
                None
            }
        })
        .collect();
    cases.sort();
    cases.into_iter().map(|c| load_fixture(&c)).collect()
}

// ── Scale helper ───────────────────────────────────────────────────────────

fn scale_artifact(html: &str, multiplier: usize) -> String {
    if multiplier <= 1 {
        return html.to_string();
    }
    if let Some(start) = html.find("<tbody>") {
        if let Some(rel_end) = html[start..].find("</tbody>") {
            let inner = &html[start + 7..start + rel_end];
            let repeated = inner.repeat(multiplier);
            return format!(
                "{}{}{}",
                &html[..start + 7],
                repeated,
                &html[start + rel_end..]
            );
        }
    }
    html.repeat(multiplier)
}

// ── Benchmarks ─────────────────────────────────────────────────────────────

fn bench_payload_sizes(c: &mut Criterion) {
    let fixtures = all_fixtures();

    eprintln!();
    eprintln!("─── Payload Size Comparison (real fixtures) ────────────────");
    for f in &fixtures {
        let art_bytes = f.artifact.len();
        eprintln!("  Case {}: artifact = {} bytes", f.case, art_bytes);
        for ops in &f.diff_replace_ops {
            let sz: usize = ops.iter().map(|o| {
                o.content.as_ref().map_or(0, |s| s.len())
            }).sum();
            eprintln!("    diff-replace:    {:>6}B ({:.1}%)", sz, sz as f64 / art_bytes as f64 * 100.0);
        }
        for ops in &f.diff_multi_ops {
            let sz: usize = ops.iter().map(|o| {
                o.content.as_ref().map_or(0, |s| s.len())
            }).sum();
            eprintln!("    diff-multi:      {:>6}B ({:.1}%)", sz, sz as f64 / art_bytes as f64 * 100.0);
        }
    }
    eprintln!("────────────────────────────────────────────────────────────");
    eprintln!();

    c.bench_function("payload_sizes_printed", |b| b.iter(|| 1 + 1));
}

fn bench_full_copy(c: &mut Criterion) {
    let fixtures = all_fixtures();
    let scales: &[usize] = &[1, 2, 3, 4];

    let mut group = c.benchmark_group("full_copy");
    group.sample_size(500);
    group.measurement_time(std::time::Duration::from_secs(10));

    for f in &fixtures {
        for &scale in scales {
            let scaled = scale_artifact(&f.artifact, scale);
            let label = format!("case_{}/{}x_{}B", f.case, scale, scaled.len());
            group.bench_with_input(BenchmarkId::from_parameter(&label), &scaled, |b, html| {
                b.iter(|| {
                    let copy = html.to_string();
                    std::hint::black_box(copy);
                })
            });
        }
    }
    group.finish();
}

fn bench_diff_replace(c: &mut Criterion) {
    let fixtures = all_fixtures();
    let scales: &[usize] = &[1, 2, 3, 4];
    let resolver = TextResolver { format: "text/html".to_string() };

    let mut group = c.benchmark_group("diff_replace");
    group.sample_size(500);
    group.measurement_time(std::time::Duration::from_secs(10));

    for f in &fixtures {
        for (i, ops) in f.diff_replace_ops.iter().enumerate() {
            for &scale in scales {
                let scaled = scale_artifact(&f.artifact, scale);
                let label = format!("case_{}/env_{}/{}x_{}B", f.case, i, scale, scaled.len());
                group.bench_with_input(BenchmarkId::from_parameter(&label), &scaled, |b, html| {
                    b.iter(|| apply_edit(&resolver, html, ops).unwrap())
                });
            }
        }
    }
    group.finish();
}

fn bench_diff_multi(c: &mut Criterion) {
    let fixtures = all_fixtures();
    let scales: &[usize] = &[1, 2, 3, 4];
    let resolver = TextResolver { format: "text/html".to_string() };

    let mut group = c.benchmark_group("diff_multi");
    group.sample_size(500);
    group.measurement_time(std::time::Duration::from_secs(10));

    for f in &fixtures {
        for (i, ops) in f.diff_multi_ops.iter().enumerate() {
            for &scale in scales {
                let scaled = scale_artifact(&f.artifact, scale);
                let label = format!("case_{}/env_{}/{}x_{}B", f.case, i, scale, scaled.len());
                group.bench_with_input(BenchmarkId::from_parameter(&label), &scaled, |b, html| {
                    b.iter(|| apply_edit(&resolver, html, ops).unwrap())
                });
            }
        }
    }
    group.finish();
}

fn bench_diff_delete(c: &mut Criterion) {
    let fixtures = all_fixtures();
    let scales: &[usize] = &[1, 2, 3, 4];
    let resolver = TextResolver { format: "text/html".to_string() };

    let mut group = c.benchmark_group("diff_delete");
    group.sample_size(500);
    group.measurement_time(std::time::Duration::from_secs(10));

    for f in &fixtures {
        for (i, ops) in f.diff_delete_ops.iter().enumerate() {
            for &scale in scales {
                let scaled = scale_artifact(&f.artifact, scale);
                let label = format!("case_{}/env_{}/{}x_{}B", f.case, i, scale, scaled.len());
                group.bench_with_input(BenchmarkId::from_parameter(&label), &scaled, |b, html| {
                    b.iter(|| apply_edit(&resolver, html, ops).unwrap())
                });
            }
        }
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_payload_sizes,
    bench_full_copy,
    bench_diff_replace,
    bench_diff_multi,
    bench_diff_delete,
);
criterion_main!(benches);
