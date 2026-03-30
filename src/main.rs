use std::path::PathBuf;
use std::sync::mpsc;
use std::time::Duration;

use artifact_generator::aap::Envelope;
use artifact_generator::store::ArtifactStore;
use artifact_generator::telemetry;
use artifact_generator::{spawn_file_watcher, spawn_render_thread, RenderMsg};
use tokio::sync::broadcast;
use tracing::{info, warn};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let guard = telemetry::init();

    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!(
            "Usage: {} <input.html> [--output output.pdf] [--protocol]",
            args[0]
        );
        std::process::exit(1);
    }

    let html_path = PathBuf::from(&args[1]);

    let mut pdf_path: Option<PathBuf> = None;
    let mut protocol_mode = false;
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--output" if i + 1 < args.len() => {
                pdf_path = Some(PathBuf::from(&args[i + 1]));
                i += 2;
            }
            "--protocol" => {
                protocol_mode = true;
                i += 1;
            }
            _ => i += 1,
        }
    }

    let pdf_path = pdf_path.unwrap_or_else(|| html_path.with_extension("pdf"));

    info!(html = %html_path.display(), pdf = %pdf_path.display(), protocol = protocol_mode, "watching");

    // Broadcast channel for file watcher -> main loop
    let (tx, mut rx) = broadcast::channel::<String>(16);
    spawn_file_watcher(tx, html_path.display().to_string(), Duration::from_millis(100));

    // mpsc channel for main loop -> render thread
    let (render_tx, render_rx) = mpsc::channel::<RenderMsg>();
    let render_handle = spawn_render_thread(render_rx, html_path.clone(), pdf_path.clone());

    let metrics = telemetry::Metrics::get();

    // Main loop: forward broadcast events to the render thread
    // In protocol mode, resolve envelopes and write resolved HTML before triggering render.
    let watched_html = html_path.clone();
    let forward = tokio::spawn(async move {
        let mut store = ArtifactStore::new(10);
        loop {
            match rx.recv().await {
                Ok(content) => {
                    if protocol_mode && Envelope::is_envelope(&content) {
                        match Envelope::from_json(&content) {
                            Ok(envelope) => {
                                info!(
                                    id = %envelope.id,
                                    version = envelope.version,
                                    mode = ?envelope.mode,
                                    "protocol envelope received"
                                );
                                match store.apply(&envelope) {
                                    Ok(resolved) => {
                                        // Write resolved HTML back to the watched file
                                        // so the renderer picks it up
                                        if let Err(e) =
                                            tokio::fs::write(&watched_html, &resolved).await
                                        {
                                            tracing::error!("failed to write resolved HTML: {e}");
                                        }
                                    }
                                    Err(e) => {
                                        tracing::error!("envelope apply failed: {e:#}");
                                    }
                                }
                            }
                            Err(e) => {
                                tracing::error!("envelope parse failed: {e}");
                            }
                        }
                    }
                    if render_tx.send(RenderMsg::Trigger).is_err() {
                        break;
                    }
                }
                Err(broadcast::error::RecvError::Lagged(n)) => {
                    warn!(lagged = n, "watcher lagged, rendering latest");
                    metrics
                        .broadcast_lag_count
                        .fetch_add(n, std::sync::atomic::Ordering::Relaxed);
                    if render_tx.send(RenderMsg::Trigger).is_err() {
                        break;
                    }
                }
                Err(broadcast::error::RecvError::Closed) => break,
            }
        }
    });

    // Wait for Ctrl+C
    tokio::signal::ctrl_c().await?;
    info!("shutting down");

    forward.abort();
    let _ = render_handle.join();

    guard.shutdown();

    Ok(())
}
