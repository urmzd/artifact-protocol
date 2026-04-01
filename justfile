build:
    cargo build

install:
    cargo install --path .

run file="/tmp/artifact.html":
    cargo run -- {{file}}

# Resolve an envelope file once and print to stdout
resolve file:
    cargo run -- {{file}}

# Watch and resolve on changes
watch file="/tmp/artifact.html":
    cargo run -- {{file}} --watch

# Stream pre-built HTML via demo script
demo file="/tmp/artifact.html": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    uv run --project tools ag-demo "$FILE"
    ./target/debug/aap "$FILE"

# Real LLM stream via ollama
demo-llm file="/tmp/artifact.html" model="gemma3": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    uv run --project tools ag-ollama "$FILE" "{{model}}"
    ./target/debug/aap "$FILE"

# Offline tokenizer benchmarks — no server needed
bench:
    uv run --project tools ag-bench

# Rust criterion benchmarks
bench-rust:
    cargo bench

# Regenerate protocol benchmark table and embed into README
bench-protocol:
    cargo run --release --bin bench-table > benches/results.md
    embed-src README.md

bench-all: bench bench-rust bench-protocol

# Stream with HF tokenizer
demo-hf tokenizer="gpt2" file="/tmp/artifact.html": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    uv run --project tools ag-hf-stream "$FILE" "{{tokenizer}}"
    ./target/debug/aap "$FILE"

test:
    cargo test
