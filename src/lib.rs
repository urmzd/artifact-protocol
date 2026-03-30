pub mod aap;
pub mod apply;
pub mod store;
pub mod telemetry;

use std::path::Path;
use std::sync::atomic::Ordering::Relaxed;
use std::sync::mpsc;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use headless_chrome::{Browser, LaunchOptions};
use tokio::fs;
use tokio::sync::broadcast;
use tokio::task::JoinHandle;
use tracing::{info, info_span, Instrument};

use crate::telemetry::Metrics;

/// Watches a file for changes and broadcasts the content on each modification.
pub fn spawn_file_watcher(
    tx: broadcast::Sender<String>,
    file_path: String,
    interval: Duration,
) -> JoinHandle<()> {
    tokio::spawn(
        async move {
            let mut last_modified = None;
            let mut tick = tokio::time::interval(interval);
            let metrics = metrics_if_init();
            loop {
                let poll_start = Instant::now();
                tick.tick().await;
                if let Ok(meta) = fs::metadata(&file_path).await {
                    let modified = meta.modified().ok();
                    if modified != last_modified {
                        last_modified = modified;
                        if let Ok(content) = fs::read_to_string(&file_path).await {
                            let file_size = content.len();
                            info!(file_size, path = %file_path, "file change detected");
                            if let Some(m) = metrics {
                                m.watcher_changes_detected.fetch_add(1, Relaxed);
                            }
                            let _ = tx.send(content);
                        }
                    }
                }
                if let Some(m) = metrics {
                    m.record_poll(poll_start.elapsed().as_secs_f64() * 1000.0);
                }
            }
        }
        .instrument(info_span!("file_watcher")),
    )
}

/// Renders HTML files to PDF using a persistent headless Chrome instance.
pub struct PdfRenderer {
    browser: Browser,
}

impl PdfRenderer {
    /// Launch a headless Chrome browser.
    pub fn new() -> Result<Self> {
        let _span = info_span!("browser_launch").entered();
        let sandbox = !std::env::var("CI").is_ok_and(|v| !v.is_empty());
        let options = LaunchOptions {
            headless: true,
            sandbox,
            ..LaunchOptions::default()
        };
        let browser = Browser::new(options).context("failed to launch headless Chrome")?;
        info!("headless Chrome launched");
        Ok(Self { browser })
    }

    /// Navigate to `html_path` (as a file:// URL) and write a PDF to `pdf_path`.
    pub fn render(&self, html_path: &Path, pdf_path: &Path) -> Result<()> {
        let _span = info_span!(
            "render_cycle",
            html_path = %html_path.display(),
            pdf_path = %pdf_path.display(),
        )
        .entered();

        let abs = std::fs::canonicalize(html_path)
            .with_context(|| format!("cannot resolve {}", html_path.display()))?;
        let url = format!("file://{}", abs.display());

        let tab = self
            .browser
            .new_tab()
            .context("failed to open new Chrome tab")?;

        let pdf_data = {
            let _nav = info_span!("navigate_and_load").entered();
            tab.navigate_to(&url)
                .context("navigation failed")?
                .wait_until_navigated()
                .context("waiting for navigation failed")?;

            let _gen = info_span!("generate_pdf").entered();
            tab.print_to_pdf(None).context("print_to_pdf failed")?
        };

        {
            let pdf_size_bytes = pdf_data.len();
            let _write = info_span!("write_pdf", pdf_size_bytes).entered();
            std::fs::write(pdf_path, &pdf_data)
                .with_context(|| format!("failed to write {}", pdf_path.display()))?;
        }

        tab.close(true).ok();

        Ok(())
    }
}

/// Messages sent to the render thread.
pub enum RenderMsg {
    /// A file change was detected; re-render.
    Trigger,
    /// Shut down the render thread.
    Shutdown,
}

/// Spawn a dedicated OS thread that owns a `PdfRenderer` and processes
/// render requests arriving on `rx`.
pub fn spawn_render_thread(
    rx: mpsc::Receiver<RenderMsg>,
    html_path: std::path::PathBuf,
    pdf_path: std::path::PathBuf,
) -> std::thread::JoinHandle<()> {
    std::thread::spawn(move || {
        let renderer = match PdfRenderer::new() {
            Ok(r) => r,
            Err(e) => {
                tracing::error!("Failed to start Chrome: {e:#}");
                return;
            }
        };

        let metrics = metrics_if_init();
        let mut render_count: u64 = 0;

        for msg in rx {
            match msg {
                RenderMsg::Trigger => {
                    render_count += 1;
                    let start = Instant::now();
                    match renderer.render(&html_path, &pdf_path) {
                        Ok(()) => {
                            let duration_ms = start.elapsed().as_secs_f64() * 1000.0;
                            let pdf_size = std::fs::metadata(&pdf_path)
                                .map(|m| m.len())
                                .unwrap_or(0);
                            info!(
                                render_count,
                                duration_ms,
                                pdf_size,
                                path = %pdf_path.display(),
                                "render complete"
                            );
                            if let Some(m) = metrics {
                                m.record_render(duration_ms, pdf_size);
                            }
                        }
                        Err(e) => {
                            tracing::error!(render_count, "render failed: {e:#}");
                        }
                    }
                }
                RenderMsg::Shutdown => break,
            }
        }
    })
}

/// Returns `Some(&Metrics)` if telemetry has been initialised, `None` otherwise.
/// This keeps benchmarks (which never call `init()`) working without overhead.
fn metrics_if_init() -> Option<&'static Metrics> {
    std::panic::catch_unwind(Metrics::get).ok()
}
