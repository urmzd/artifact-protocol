build:
    cargo build

test:
    cargo test

# Rust criterion micro-benchmarks (apply engine performance)
bench-rust:
    cargo bench

# Generate benchmark table and embed into README
bench-protocol:
    cargo run --release --bin bench_table > benches/results.md

# Generate experiment input directories (no LLM needed)
bench-generate count="0":
    cd benches && go run . generate $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Run a single experiment (requires Ollama or API key)
bench-single n="1" model="qwen3.5:4b":
    cd benches && go run . run --single {{n}} --model {{model}}

# Run all experiments
bench model="qwen3.5:4b" count="0":
    cd benches && go run . run --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

bench-all: bench-rust bench-protocol
