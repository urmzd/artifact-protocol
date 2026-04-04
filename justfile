build:
    cargo build

test:
    cargo test

# Rust criterion micro-benchmarks (apply engine speed)
bench:
    cargo bench

# Sync workspace — builds Rust FFI via maturin + all Python packages
bind:
    uv sync

# Run conversation benchmark experiments (base vs GAP flows)
run count="0" model="" id="" provider="google" fallback="":
    uv run gap-evals run --provider {{provider}} $(if [ "{{model}}" != "" ]; then echo "--model {{model}}"; fi) $(if [ "{{count}}" != "0" ]; then echo "--count {{count}}"; fi) $(if [ "{{id}}" != "" ]; then echo "--id {{id}}"; fi) $(if [ "{{fallback}}" != "" ]; then echo "--fallback {{fallback}}"; fi)

# Generate markdown report from experiment metrics
report:
    uv run gap-evals report
