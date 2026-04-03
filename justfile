build:
    cargo build

test:
    cargo test

# Rust criterion micro-benchmarks (apply engine speed)
bench:
    cargo bench

# Generate benchmark corpus (artifacts + envelopes via Ollama)
generate count="0" model="gemma4":
    cd evals && uv run aap-evals generate --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Run baseline vs AAP experiment (LLM quality eval)
experiment count="0" model="gemma4":
    cd evals && uv run aap-evals experiment --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Generate experiment report (markdown)
report:
    cd evals && uv run aap-evals report
