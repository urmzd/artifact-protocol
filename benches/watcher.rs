use std::time::Duration;

use criterion::{criterion_group, criterion_main, Criterion};
use tokio::sync::broadcast;

use aap::spawn_file_watcher;

fn watcher_detect_change(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();

    c.bench_function("watcher_detect_change", |b| {
        b.iter(|| {
            rt.block_on(async {
                let tmp = tempfile::NamedTempFile::new().unwrap();
                let path = tmp.path().to_str().unwrap().to_string();

                // Write initial content so the file exists
                tokio::fs::write(&path, "<h1>initial</h1>").await.unwrap();

                let (tx, mut rx) = broadcast::channel::<String>(16);

                let handle =
                    spawn_file_watcher(tx, path.clone(), Duration::from_millis(10));

                // Wait for initial read
                let _ = rx.recv().await;

                // Write new content and measure detection
                tokio::fs::write(&path, "<h1>changed</h1>").await.unwrap();
                let _ = rx.recv().await;

                handle.abort();
            });
        });
    });
}

fn broadcast_throughput(c: &mut Criterion) {
    let html_payload = "<div>".repeat(1024); // ~6KB payload

    c.bench_function("broadcast_throughput", |b| {
        b.iter(|| {
            let (tx, mut rx) = broadcast::channel::<String>(16);
            tx.send(html_payload.clone()).unwrap();
            let _ = rx.try_recv().unwrap();
        });
    });
}

criterion_group!(benches, watcher_detect_change, broadcast_throughput);
criterion_main!(benches);
