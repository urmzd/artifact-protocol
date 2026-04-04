use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
use std::sync::OnceLock;

use opentelemetry::trace::TracerProvider;
use tracing_opentelemetry::OpenTelemetryLayer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::EnvFilter;

/// Metric instruments accessible from anywhere via `Metrics::get()`.
pub struct Metrics {
    pub envelope_apply_count: AtomicU64,
    envelope_apply_duration_sum_us: AtomicU64,
    envelope_apply_duration_min_us: AtomicU64,
    envelope_apply_duration_max_us: AtomicU64,
    pub watcher_changes_detected: AtomicU64,
    watcher_poll_count: AtomicU64,
    watcher_poll_sum_us: AtomicU64,
    watcher_poll_min_us: AtomicU64,
    watcher_poll_max_us: AtomicU64,
    pub broadcast_lag_count: AtomicU64,
}

static METRICS: OnceLock<Metrics> = OnceLock::new();

impl Metrics {
    /// Returns the global metrics instruments. Panics if `init()` was not called.
    pub fn get() -> &'static Metrics {
        METRICS.get().expect("telemetry not initialised")
    }

    fn new() -> Self {
        Self {
            envelope_apply_count: AtomicU64::new(0),
            envelope_apply_duration_sum_us: AtomicU64::new(0),
            envelope_apply_duration_min_us: AtomicU64::new(u64::MAX),
            envelope_apply_duration_max_us: AtomicU64::new(0),
            watcher_changes_detected: AtomicU64::new(0),
            watcher_poll_count: AtomicU64::new(0),
            watcher_poll_sum_us: AtomicU64::new(0),
            watcher_poll_min_us: AtomicU64::new(u64::MAX),
            watcher_poll_max_us: AtomicU64::new(0),
            broadcast_lag_count: AtomicU64::new(0),
        }
    }

    /// Record a completed envelope apply.
    pub fn record_apply(&self, duration_ms: f64) {
        self.envelope_apply_count.fetch_add(1, Relaxed);
        let us = (duration_ms * 1000.0) as u64;
        self.envelope_apply_duration_sum_us.fetch_add(us, Relaxed);
        self.envelope_apply_duration_min_us.fetch_min(us, Relaxed);
        self.envelope_apply_duration_max_us.fetch_max(us, Relaxed);
    }

    /// Record a watcher poll duration.
    pub fn record_poll(&self, duration_ms: f64) {
        self.watcher_poll_count.fetch_add(1, Relaxed);
        let us = (duration_ms * 1000.0) as u64;
        self.watcher_poll_sum_us.fetch_add(us, Relaxed);
        self.watcher_poll_min_us.fetch_min(us, Relaxed);
        self.watcher_poll_max_us.fetch_max(us, Relaxed);
    }
}

/// Guard returned by `init()`. Call `shutdown()` to print the metrics summary.
pub struct TelemetryGuard;

/// Initialise tracing + metrics. Call once at startup.
pub fn init() -> TelemetryGuard {
    METRICS.get_or_init(Metrics::new);

    let tracer_provider = opentelemetry_sdk::trace::SdkTracerProvider::builder().build();
    let tracer = tracer_provider.tracer("gap");
    let otel_layer = OpenTelemetryLayer::new(tracer);

    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("gap=info"));

    tracing_subscriber::registry()
        .with(env_filter)
        .with(
            tracing_subscriber::fmt::layer()
                .compact()
                .with_writer(std::io::stderr),
        )
        .with(otel_layer)
        .init();

    TelemetryGuard
}

impl TelemetryGuard {
    /// Print a human-readable metrics summary table to stderr.
    pub fn shutdown(self) {
        let m = Metrics::get();

        eprintln!();
        eprintln!(
            "\u{2500}\u{2500} Metrics Summary \u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}"
        );

        let ac = m.envelope_apply_count.load(Relaxed);
        eprintln!("{:<30}{}", "envelope.apply_count", ac);

        if ac > 0 {
            let sum = m.envelope_apply_duration_sum_us.load(Relaxed) as f64 / 1000.0;
            let min = m.envelope_apply_duration_min_us.load(Relaxed) as f64 / 1000.0;
            let max = m.envelope_apply_duration_max_us.load(Relaxed) as f64 / 1000.0;
            let avg = sum / ac as f64;
            eprintln!(
                "{:<30}avg={:<10.1} min={:<10.1} max={:.1}",
                "envelope.apply_duration_ms", avg, min, max
            );
        }

        eprintln!(
            "{:<30}{}",
            "watcher.changes_detected",
            m.watcher_changes_detected.load(Relaxed)
        );

        let pc = m.watcher_poll_count.load(Relaxed);
        if pc > 0 {
            let sum = m.watcher_poll_sum_us.load(Relaxed) as f64 / 1000.0;
            let min = m.watcher_poll_min_us.load(Relaxed) as f64 / 1000.0;
            let max = m.watcher_poll_max_us.load(Relaxed) as f64 / 1000.0;
            let avg = sum / pc as f64;
            eprintln!(
                "{:<30}avg={:<10.1} min={:<10.1} max={:.1}",
                "watcher.poll_duration_ms", avg, min, max
            );
        }

        eprintln!(
            "{:<30}{}",
            "broadcast.lag_count",
            m.broadcast_lag_count.load(Relaxed)
        );

        eprintln!(
            "\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}"
        );
    }
}
