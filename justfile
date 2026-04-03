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

# Run conversation benchmark experiments (base vs AAP flows)
run count="0" model="gemma4" id="" provider="ollama":
    cd evals && uv run aap-evals run --provider {{provider}} --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi) $(if [ "{{id}}" != "" ]; then echo "--id {{id}}"; fi)

# Generate markdown report from experiment metrics
report:
    cd evals && uv run aap-evals report
