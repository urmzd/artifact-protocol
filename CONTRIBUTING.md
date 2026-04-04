# Contributing

Contributions are welcome. Please follow these guidelines.

## Getting started

```sh
git clone https://github.com/urmzd/generative-artifact-protocol
cd generative-artifact-protocol
just build   # compile the Rust library
just test    # run unit tests
just bench   # run criterion benchmarks
```

## Project structure

```
generative-artifact-protocol/
├── src/
│   ├── lib.rs                 # crate root (re-exports modules)
│   ├── gap.rs                 # envelope data model
│   ├── apply.rs               # stateless apply engine
│   ├── store.rs               # versioned artifact store
│   ├── markers.rs             # section marker utilities
│   ├── telemetry.rs           # tracing and metrics
│   └── ffi.rs                 # Python bindings (optional, pyo3)
├── evals/                     # LLM evaluation framework
│   ├── pyproject.toml         # Python dependencies (uv + maturin)
│   └── src/gap_evals/         # Eval CLI and harness
├── spec/                      # Protocol specification
│   ├── gap.md                 # Main spec (v0.1)
│   ├── gap-sse.md             # SSE wire format binding
│   ├── schemas/               # JSON Schema files
│   └── examples/              # Example envelopes
├── benches/                   # Criterion benchmarks
├── justfile                   # Task recipes
└── .github/workflows/         # CI (build + test) and release
```

## Making changes

- **Apply engine** (`src/apply.rs`): stateless function that resolves envelopes. Keep it pure — no I/O, no side effects.
- **Store** (`src/store.rs`): versioned artifact store with control-plane envelopes.
- **Evals** (`evals/`): LLM evaluation framework for measuring token efficiency. See `evals/README.md`.
- **New recipes**: add them to `justfile` with a comment describing what they do.

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make your changes and ensure `just test` passes.
3. Open a pull request with a clear description of what changed and why.

## Code style

- Rust: `cargo fmt` before committing.

## License

By contributing you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
