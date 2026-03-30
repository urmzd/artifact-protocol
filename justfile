build:
    cargo build

install:
    cargo install --path .

run file="/tmp/artifact.html":
    cargo run -- {{file}}

# Sanity test: stream pre-built HTML, verify PDF is produced
demo file="/tmp/artifact.html": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    ./target/debug/artifact-generator "$FILE" &
    PID=$!
    sleep 0.3
    uv run --project tools ag-demo "$FILE"
    sleep 2  # let final render complete
    kill $PID 2>/dev/null || true
    PDF="${FILE%.html}.pdf"
    echo "PDF written to $PDF"

# Real LLM stream via ollama
demo-llm file="/tmp/artifact.html" model="gemma3": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    ./target/debug/artifact-generator "$FILE" &
    PID=$!
    sleep 0.3
    uv run --project tools ag-ollama "$FILE" "{{model}}"
    sleep 2
    kill $PID 2>/dev/null || true
    PDF="${FILE%.html}.pdf"
    echo "PDF written to $PDF"

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

# Stream with HF tokenizer
demo-hf tokenizer="gpt2" file="/tmp/artifact.html": build
    #!/usr/bin/env bash
    set -e
    FILE="{{file}}"
    ./target/debug/artifact-generator "$FILE" &
    PID=$!
    sleep 0.3
    uv run --project tools ag-hf-stream "$FILE" "{{tokenizer}}"
    sleep 2
    kill $PID 2>/dev/null || true
    PDF="${FILE%.html}.pdf"
    echo "PDF written to $PDF"

test: build
    #!/usr/bin/env bash
    set -e
    TEST_FILE=$(mktemp /tmp/artifact-test-XXXX.html)
    echo "<h1>just test</h1>" > "$TEST_FILE"
    PDF="${TEST_FILE%.html}.pdf"
    ./target/debug/artifact-generator "$TEST_FILE" --output "$PDF" &
    PID=$!
    sleep 3  # give Chrome time to start and render
    kill "$PID" 2>/dev/null || true
    if [ -s "$PDF" ]; then
        echo "PASS: PDF exists and is non-empty ($(wc -c < "$PDF") bytes)"
    else
        echo "FAIL: PDF not found or empty"
        rm -f "$TEST_FILE" "$PDF"
        exit 1
    fi
    rm -f "$TEST_FILE" "$PDF"
