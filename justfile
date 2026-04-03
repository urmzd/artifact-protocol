build:
    cargo build

test:
    cargo test

# Rust criterion micro-benchmarks (apply engine performance)
bench-rust:
    cargo bench

# Generate experiment input directories (no LLM needed)
bench-generate count="0":
    cd evals && uv run aap-evals generate $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Run a single experiment (requires Ollama)
bench-single n="1" model="qwen3.5:4b":
    cd evals && uv run aap-evals run --single {{n}} --model {{model}}

# Run all experiments
bench model="qwen3.5:4b" count="0":
    cd evals && uv run aap-evals run --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Generate apply-engine benchmark corpus (artifacts + envelopes via Ollama)
corpus count="0" model="gemma4":
    cd evals && uv run aap-evals generate-corpus --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Run apply-engine benchmarks against corpus
bench-apply:
    cd evals && uv run aap-evals bench

# Generate apply-engine benchmark report
bench-report:
    cd evals && uv run aap-evals report

# Evaluation reports
eval-cost:
    cd evals && uv run aap-evals eval-cost

eval-reliability:
    cd evals && uv run aap-evals eval-reliability

eval-similarity:
    cd evals && uv run aap-evals eval-similarity

eval: eval-cost eval-reliability eval-similarity

bench-all: bench-rust
