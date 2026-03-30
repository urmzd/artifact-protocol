# artifact-generator

A local dev tool that watches an HTML file on disk and continuously renders it to PDF using headless Chrome. Designed for streaming HTML artifacts token-by-token — useful for benchmarking tokenizers, LLM streaming, and any chunked-write workflow.

Includes the **[Agent-Artifact Protocol (AAP)](spec/aap.md)** — an open standard for token-efficient artifact generation, updates, and streaming. The protocol defines how LLMs can declare, diff, and reprovision artifacts with minimal token expenditure (90-99% savings on updates).

## How it works

1. The Rust binary watches a file on disk (polling every 100 ms).
2. On every change it renders the HTML to PDF via headless Chrome.
3. The PDF is overwritten in place on each render cycle.

```
writer (Python) ──writes──▶ file.html ──render──▶ file.pdf
                                        ▲
                              artifact-generator (Rust + headless Chrome)
```

## Requirements

- [Rust](https://rustup.rs/) (stable)
- [Google Chrome](https://www.google.com/chrome/) or Chromium (headless rendering)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [just](https://github.com/casey/just) (optional, for recipes)

## Quick start

```sh
# Build the binary
just build

# Stream a pre-built HTML dashboard and produce a PDF
just demo

# Stream via a real LLM (requires ollama)
just demo-llm

# Stream via a HuggingFace tokenizer (gpt2 by default)
just demo-hf

# Stream with BERT tokenizer
just demo-hf tokenizer=bert-base-uncased

# Run offline tokenizer benchmarks (no server needed)
just bench

# Run Rust criterion benchmarks (file watcher, broadcast throughput)
just bench-rust
```

## CLI usage

```sh
artifact-generator <input.html> [--output output.pdf] [--protocol]
```

- `<input.html>` — the HTML file to watch.
- `--output` — optional PDF output path (defaults to `<input>.pdf`).
- `--protocol` — enable [Agent-Artifact Protocol (AAP)](spec/aap.md) mode. When the watched file contains a protocol envelope (JSON with `"protocol": "aap/1.0"`), the binary resolves the envelope (applying diffs, section updates, or templates) and renders the resolved HTML.

The process runs until interrupted with Ctrl+C.

## Observability

The Rust binary emits structured log lines to stderr via `tracing` and prints a metrics summary on shutdown.

### Structured logging

Logs use `tracing-subscriber` (compact format with timestamps). Control verbosity with the `RUST_LOG` environment variable (default: `artifact_generator=info`).

```sh
# Show debug-level spans
RUST_LOG=artifact_generator=debug artifact-generator input.html
```

### Tracing spans

| Span | Location |
|---|---|
| `file_watcher` | File polling loop |
| `browser_launch` | Headless Chrome startup |
| `render_cycle` | Full render (navigate + PDF + write) |
| `navigate_and_load` | Chrome tab navigation |
| `generate_pdf` | `print_to_pdf` call |
| `write_pdf` | PDF file write |

### Metrics summary

On Ctrl+C the binary prints a summary table to stderr:

```
── Metrics Summary ───────────────────────────────────
render.count                  5
render.duration_ms            avg=245.3      min=120.1      max=450.7
render.pdf_size_bytes         avg=83412      min=81000      max=86200
watcher.changes_detected      5
watcher.poll_duration_ms      avg=0.1        min=0.0        max=0.3
broadcast.lag_count           0
───────────────────────────────────────────────────────
```

## Recipes

| Recipe | Description |
|---|---|
| `just build` | Compile the Rust binary |
| `just install` | Install the binary via `cargo install` |
| `just demo` | Stream a pre-built HTML dashboard, produce PDF |
| `just demo-llm [model]` | Live ollama LLM streaming (default: gemma3) |
| `just demo-hf [tokenizer]` | HuggingFace tokenizer streaming |
| `just bench` | Offline Python tokenizer benchmarks |
| `just bench-rust` | Rust criterion benchmarks (watcher, broadcast) |
| `just test` | Smoke test: verify PDF output is produced |

## Tools package

The Python scripts live under `tools/` and are structured as a proper package (`artifact_generator`) with console entry points:

| Entry point | Description |
|---|---|
| `ag-demo` | Stream a pre-built HTML dashboard in fixed chunks |
| `ag-ollama` | Stream a live LLM response via ollama |
| `ag-stream` | Generic file streaming utility |
| `ag-hf-stream` | Stream via a HuggingFace tokenizer |
| `ag-bench` | Offline benchmark: tokenize time, token count, throughput |
| `ag-realtime` | Real-time streaming dashboard |
| `ag-aap-demo` | AAP lifecycle demo (full → diff → section → template) |
| `ag-aap-bench` | Token savings benchmark across AAP generation modes |
| `ag-parallel-demo` | Parallel manifest generation demo (concurrent sections + assembly) |

Install and run any entry point with:

```sh
uv run --project tools ag-bench
```

## AAP benchmarks

Payload size and apply time for each [Agent-Artifact Protocol (AAP)](spec/aap.md) generation mode, measured against an 8 KB HTML dashboard fixture. Regenerate with `cargo run --release --bin bench-table > benches/results.md`.

<!-- embed-src src="benches/results.md" -->
| Mode | Scenario | Payload | % of Full | Savings | Apply Time |
|---|---|---:|---:|---:|---:|
| **full** | Full regeneration (baseline) | 8,164 B | 100.0% | — | 0 ns |
| **diff** | 1 value change | 12 B | 0.1% | **99.9%** | 822 ns |
| **diff** | 4 value changes | 50 B | 0.6% | **99.4%** | 2.7 µs |
| **section** | 1 section replaced | 441 B | 5.4% | **94.6%** | 1.1 µs |
| **section** | 2 sections replaced | 516 B | 6.3% | **93.7%** | 3.4 µs |
| **template** | 8 slot bindings | 141 B | 1.7% | **98.3%** | 2.7 µs |
| **manifest** | 4 sections assembled | 487 B | 6.0% | **94.0%** | 1.8 µs |
<!-- /embed-src -->

## Tokenizer benchmarks (example)

```
Tokenizer                    Tokens  Avg ch/tok    Tok ms   Tokens/sec
────────────────────────────────────────────────────────────────────────
gpt2                         27,300         2.4      14.2       1,917k
bert-base-uncased            33,628         1.9      16.1       2,094k
Fixed 30-char chunks          2,169        30.0       0.1      23,220k
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
