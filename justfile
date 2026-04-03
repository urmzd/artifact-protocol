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

# Run baseline vs AAP experiment (LLM quality eval — apply-engine corpus)
experiment count="0" model="gemma4":
    cd evals && uv run aap-evals experiment --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi)

# Run conversation benchmark experiments (base vs AAP flows)
run count="0" model="gemma4" id="":
    cd evals && uv run aap-evals run --model {{model}} $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi) $(if [ "{{id}}" != "" ]; then echo "--id {{id}}"; fi)

# Generate experiment report (markdown)
report:
    cd evals && uv run aap-evals report
