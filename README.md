# aap

> **Warning**: This project is `v0` — the protocol, schemas, and APIs are subject to breaking changes without notice until a formal release.

An open standard for token-efficient artifact updates and streaming — the **[Agent-Artifact Protocol (AAP)](spec/aap.md)**. The protocol defines how LLMs can declare, diff, and reprovision text artifacts with minimal token expenditure — 90-99% output token reduction per update, translating to 43-86% total cost savings depending on the model's pricing (see [cost model](spec/aap.md#811-cost-model)).

Includes a Rust reference implementation of the **apply engine** — a stateless, deterministic function that resolves protocol envelopes into artifact content — plus a Python evaluation framework for measuring token efficiency against real LLM runs.

## How it works

1. An LLM produces an artifact envelope (JSON) — either a `synthesize` envelope (full content with target markers) or an `edit` envelope (targeted changes by ID or JSON Pointer).
2. The apply engine resolves the envelope against the current artifact state to produce the updated artifact and a lightweight handle.
3. The orchestrator holds handles; the resolved artifact (HTML, SVG, source code, config, etc.) is stored and consumed by downstream tools — browsers, IDEs, etc.

```
LLM ──produces──▶ envelope ──apply──▶ (artifact, handle)
                                 ▲
                           aap (stateless, ~2μs)
```

> AAP produces text artifacts; rendering is a consumer responsibility.

## Apply engine

The core of the library is a single stateless function:

```rust
pub fn apply(artifact: Option<&Artifact>, envelope: &Envelope) -> Result<(Artifact, Envelope)>
```

It takes the current artifact (if any) and an operation envelope, and returns the updated artifact plus a handle envelope. Three envelope types:

| Envelope | Direction | Description |
|---|---|---|
| **synthesize** | input | Complete artifact content (baseline or reset) with `<aap:target>` markers |
| **edit** | input | Targeted changes via ID (`<aap:target>` markers) or JSON Pointer |
| **handle** | output | Lightweight reference returned after every synthesize or edit |

The function is pure — no I/O, no state, no side effects. This makes it portable: embed it in browsers (via WASM), IDEs, CLI tools, or service backends.

## Requirements

- [Rust](https://rustup.rs/) (stable)
- [uv](https://github.com/astral-sh/uv) (Python package manager, for evals)
- [just](https://github.com/casey/just) (optional, for recipes)

## Quick start

```sh
# Build the library
just build

# Run tests
just test

# Run Rust criterion benchmarks (apply engine speed)
just bench
```

## Recipes

| Recipe | Description |
|---|---|
| `just build` | Compile the Rust library |
| `just test` | Run Rust unit tests |
| `just bench` | Rust criterion micro-benchmarks (apply engine speed) |
| `just generate [count] [model]` | Generate benchmark corpus (artifacts + envelopes via Ollama) |
| `just experiment [count] [model]` | Run baseline vs AAP experiment (LLM quality eval) |
| `just run [count] [model] [id]` | Run conversation benchmark experiments (base vs AAP flows) |
| `just report` | Generate experiment report (markdown) |

## Evals

The `evals/` directory contains an evaluation framework that measures AAP's token efficiency and envelope reliability against real LLM runs. See [`evals/README.md`](evals/README.md) for details.

## Cost model

AAP saves tokens by replacing full artifact regeneration with small diff envelopes. The savings are real but **LLM-dependent** — they vary with the model's tokenizer, output/input price ratio, and whether a cheaper model handles diffs. See the [full derivation in the spec](spec/aap.md#811-cost-model).

**The mechanism:** the maintain context reads the full artifact ($S$ input tokens) and produces an edit envelope ($d$ output tokens, where $d$ is typically 1–5% of $S$). The apply engine resolves the edit at zero token cost (CPU, ~2μs). The orchestrator never reads the artifact at all — it holds only lightweight handles.

- **Output token reduction:** $d$ instead of $S$ per edit (95–99% fewer output tokens)
- **Context flattening:** no conversation history accumulates — each edit reads only the current artifact ($S$), not all prior versions ($k \cdot S$ at edit $k$ in a naive conversation)
- **Model asymmetry:** the maintain context can use a cheaper model, multiplying savings further

**Concrete example** (2,000-token artifact, 30-token edit, $r = p_{\text{out}}/p_{\text{in}} = 4\text{x}$):

| After $N$ edits | Naive conversation | AAP | Total savings |
|---:|---:|---:|---:|
| 1 | \$0.071 | \$0.039 | 45% |
| 5 | \$0.304 | \$0.070 | 77% |
| 10 | \$0.763 | \$0.107 | 86% |

At $r = 1$ (equal pricing), the same scenario yields ~49% savings after 10 edits. At $r = 5$, it reaches ~87%. The output token reduction is constant — what changes is how much of total cost it represents.

## AAP payload benchmarks

Payload size and apply time for each [Agent-Artifact Protocol (AAP)](spec/aap.md) envelope type, measured against an 8 KB HTML dashboard fixture.

> **Note:** The "Payload savings" column measures **byte reduction** in the envelope payload — a proxy for output token reduction but not identical (tokenizers vary). Actual cost savings depend on the model's output/input price ratio; see [cost model](spec/aap.md#711-cost-model) for the full derivation.

<!-- embed-src src="benches/results.md" -->
| Envelope | Scenario | Payload | % of Full | Payload savings | Apply Time |
|---|---|---:|---:|---:|---:|
| **synthesize** | Full generation (baseline) | 8,164 B | 100.0% | — | 1 ns |
| **edit** | 1 value replace (ID targeting) | 12 B | 0.1% | **99.9%** | 1.5 µs |
| **edit** | 4 value replaces (ID targeting) | 50 B | 0.6% | **99.4%** | 3.5 µs |
| **edit** | 1 section replace (ID targeting) | 441 B | 5.4% | **94.6%** | 1.4 µs |
| **edit** | 2 section replaces (ID targeting) | 516 B | 6.3% | **93.7%** | 3.8 µs |
<!-- /embed-src -->

## License

This project is dual-licensed:

- **Code** (`src/`, `evals/`, `benches/`, build files) — [Apache License 2.0](LICENSE)
- **Specification & docs** (`spec/`, `assets/`, documentation) — [CC-BY 4.0](LICENSE-CC-BY-4.0)

See [NOTICE](NOTICE) for details. Attribution is required under both licenses.
