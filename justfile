build:
    cargo build

test:
    cargo test

# Rust criterion micro-benchmarks (apply engine speed)
bench:
    cargo bench

# Build Rust FFI and install into evals venv
bind:
    cd evals && uv sync && uv run maturin develop --manifest-path ../Cargo.toml -F python && cp .venv/lib/python3.12/site-packages/aap/aap.cpython-*-darwin.so src/aap_evals/ 2>/dev/null || true

# Generate benchmark corpus (artifacts + envelopes via LLM)
generate count="0" model="" id="" provider="google" fallback="":
    cd evals && uv run aap-evals generate --provider {{provider}} $(if [ "{{model}}" != "" ]; then echo "--model {{model}}"; fi) $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi) $(if [ "{{fallback}}" != "" ]; then echo "--fallback {{fallback}}"; fi)

# Run conversation benchmark experiments (base vs AAP flows)
run count="0" model="" id="" provider="google" fallback="":
    cd evals && uv run aap-evals run --provider {{provider}} $(if [ "{{model}}" != "" ]; then echo "--model {{model}}"; fi) $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi) $(if [ "{{id}}" != "" ]; then echo "--id {{id}}"; fi) $(if [ "{{fallback}}" != "" ]; then echo "--fallback {{fallback}}"; fi)

# Generate markdown report from experiment metrics
report:
    cd evals && uv run aap-evals report
