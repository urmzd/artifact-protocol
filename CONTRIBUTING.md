# Contributing

Contributions are welcome. Please follow these guidelines.

## Getting started

```sh
git clone https://github.com/urmzd/aap
cd aap
just build   # compile the Rust binary
just test    # run the smoke test
just bench   # run offline tokenizer benchmarks
```

## Project structure

```
aap/
├── src/
│   ├── main.rs               # CLI entry point, signal handling
│   ├── lib.rs                 # File watcher
│   └── telemetry.rs           # Tracing init, metrics collection, shutdown summary
├── tools/
│   ├── pyproject.toml         # Python dependencies (uv)
│   └── src/aap/
│       ├── __init__.py        # Package exports (tokenizer factory, corpus)
│       ├── corpus.py          # HTML corpus generator
│       ├── scripts/           # Streaming demos (demo, ollama, realtime)
│       ├── benchmarks/        # Tokenizer benchmarks (run, hf_stream)
│       └── assets/            # Pre-built HTML dashboard
├── benches/watcher.rs         # Criterion benchmarks
├── justfile                   # Task recipes
└── .github/workflows/ci.yml   # CI (Rust build + Python benchmarks)
```

## Making changes

- **Rust binary** (`src/`): file watcher, apply engine, telemetry. Keep dependencies light.
- **Telemetry** (`src/telemetry.rs`): structured logging via `tracing`, metrics summary on shutdown.
- **Python tools** (`tools/`): streaming scripts and benchmarks. Import `build_html()` from `corpus.py` rather than duplicating the corpus.
- **New tokenizers**: add them to the `TOKENIZERS` list in `tools/src/aap/benchmarks/run.py`.
- **New recipes**: add them to `justfile` with a comment describing what they do.

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make your changes and ensure `just test` passes.
3. For Python changes, run `just bench` to confirm benchmarks still execute.
4. Open a pull request with a clear description of what changed and why.

## Code style

- Rust: `cargo fmt` before committing.
- Python: keep scripts self-contained and runnable via `uv run --project tools`.

## License

By contributing you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
