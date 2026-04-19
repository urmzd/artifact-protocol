<p align="center">
  <h1 align="center">Generative Artifact Protocol</h1>
  <p align="center">
    Token-efficient artifact updates and streaming for LLMs — up to 99% fewer output tokens per edit.
    <br /><br />
    <a href="https://crates.io/crates/generative-artifact-protocol">Crates.io</a>
    &middot;
    <a href="https://github.com/urmzd/generative-artifact-protocol/issues">Report Bug</a>
    &middot;
    <a href="spec/gap.md">Specification</a>
  </p>
</p>

<p align="center">
  <a href="https://github.com/urmzd/generative-artifact-protocol/actions/workflows/ci.yml"><img src="https://github.com/urmzd/generative-artifact-protocol/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://crates.io/crates/generative-artifact-protocol"><img src="https://img.shields.io/crates/v/generative-artifact-protocol" alt="crates.io"></a>
  &nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/github/license/urmzd/generative-artifact-protocol" alt="License"></a>
</p>

> **Warning**: This project is `v0` — the protocol, schemas, and APIs are subject to breaking changes without notice until a formal release.

An open standard protocol — **[GAP](spec/gap.md)** — that lets LLMs declare, diff, and reprovision text artifacts with minimal token expenditure. Includes a Rust reference implementation of the apply engine plus an evaluation CLI for measuring token efficiency against real LLM runs.

## Features

- **Envelope system** — three operation types (`synthesize`, `edit`, `handle`) for full generation, targeted updates, and lightweight references
- **Stateless apply engine** — pure function, no I/O, ~2μs per edit; portable to browsers (WASM), IDEs, CLIs, or service backends
- **ID-based targeting** — `<gap:target id="ID">` markers and JSON Pointer paths eliminate hallucinated search strings
- **Format-agnostic** — works with HTML, Python, JavaScript, JSON, YAML, Rust, Go, SVG, and more
- **Up to 99% output token reduction** per edit — actual reduction depends on edit scope: ~95-99% for value changes, ~80-95% for section rewrites; total cost savings depend on model pricing ratio and edit history ([cost model](spec/gap.md#711-cost-model))
- **SSE transport binding** — wire format for streaming with reconnection support ([GAP-SSE](spec/gap-sse.md))
- **Evaluation framework** — 90 experiment datasets measuring token efficiency and reliability against real LLM runs

## Install

**Rust crate:**

```sh
cargo add generative-artifact-protocol
```

**From source (full workspace):**

```sh
git clone https://github.com/urmzd/generative-artifact-protocol
cd generative-artifact-protocol
```

Requires [Rust](https://rustup.rs/) (stable) and optionally [just](https://github.com/casey/just) (for recipes).

## Quick Start

```sh
# Build the Rust library
just build

# Run tests
just test

# Run criterion benchmarks (apply engine speed)
just bench

# Build the eval CLI (release)
just build-eval

# Run LLM evaluations
just run count=5 model="gemini-2.0-flash"

# Generate report from experiment metrics
just report
```

## Usage

### How it works

```
LLM ──produces──▶ envelope ──apply──▶ (artifact, handle)
                                 ▲
                           gap (stateless, ~2μs)
```

1. An LLM produces an artifact envelope (JSON) — either a `synthesize` envelope (full content with target markers) or an `edit` envelope (targeted changes by ID or JSON Pointer).
2. The apply engine resolves the envelope against the current artifact state to produce the updated artifact and a lightweight handle.
3. The orchestrator holds handles; the resolved artifact is stored and consumed by downstream tools — browsers, IDEs, etc.

### Apply engine

The core of the library is a single stateless function:

```rust
pub fn apply(artifact: Option<&Artifact>, envelope: &Envelope) -> Result<(Artifact, Envelope)>
```

| Envelope | Direction | Description |
|---|---|---|
| **synthesize** | input | Complete artifact content (baseline or reset) with `<gap:target>` markers |
| **edit** | input | Targeted changes via ID (`<gap:target>` markers) or JSON Pointer |
| **handle** | output | Lightweight reference returned after every synthesize or edit |

### Recipes

| Recipe | Description |
|---|---|
| `just build` | Compile the Rust library |
| `just test` | Run Rust unit tests |
| `just bench` | Criterion micro-benchmarks (apply engine speed) |
| `just build-eval` | Build the eval CLI (release) |
| `just run [count] [model] [id] [flow] [api-base] [api-key]` | Run conversation benchmark experiments (base vs GAP flows) |
| `just report` | Generate markdown report from experiment metrics |
| `just score` | Retroactive quality scoring of experiment results |

### Cost model

GAP saves tokens by replacing full artifact regeneration with small edit envelopes. The actual savings are **not deterministic** — they depend on edit scope, how efficiently the LLM generates envelopes, the model's tokenizer, and pricing. The LLM may produce larger-than-minimal edits or fall back to full regeneration. The estimates below assume well-formed, targeted edits. See the [full derivation in the spec](spec/gap.md#711-cost-model).

In a naive conversation, each turn's input carries everything: instructions, all prior artifact versions, all prior messages, and the current request — growing quadratically with edit count. GAP's maintain context is **stateless**: each call starts fresh with only the instructions ($I$), the current artifact ($S$), and the edit request. It produces a small edit envelope ($d$ output tokens) and terminates. The apply engine resolves the edit deterministically (CPU, ~2μs, zero tokens). Three effects compound:

- **Input token reduction:** a naive conversation at edit $k$ reads $I + S_0 + S_1 + \ldots + S_{k-1}$ — every prior version. GAP reads only $I + S_{k-1}$ — the current artifact. At 10 edits, this is ~78% fewer input tokens.
- **Output token reduction:** the LLM produces $d$ tokens instead of $S$ per edit — only the changed content plus a constant envelope overhead (JSON structure, target IDs). $d$ scales with the size of the change, not the size of the artifact. A two-value edit on a 2,000-token artifact produces ~30 tokens; a section rewrite produces hundreds. Either way, unchanged content is never regenerated.
- **Model asymmetry:** the maintain context can use a cheaper model than the orchestrator, multiplying savings further.

**Projected example** — using a reference model at \$3/M input, \$15/M output ($r = 5$), with a 2,000-token artifact, 30-token edit envelope, and 500 instruction tokens:

| After $N$ edits | Naive conversation | GAP | Estimated savings |
|---:|---:|---:|---:|
| 1 | \$0.069 | \$0.039 | ~43% |
| 5 | \$0.279 | \$0.071 | ~75% |
| 10 | \$0.677 | \$0.111 | ~84% |

> These figures assume ideal edit behavior ($d = 30$ tokens per edit). Actual savings vary — larger edits, section-level rewrites, or model-specific tokenization will shift these numbers. Savings also scale with $r$: at $r = 1$ (equal pricing), per-edit savings drop to ~44%; at $r = 5$, they reach ~79%.

### Payload benchmarks

Payload size and apply time for each envelope type, measured against an 8 KB HTML dashboard fixture.

> **Note:** "Payload savings" measures **byte reduction** — a proxy for output token reduction but not identical (tokenizers vary). See [cost model](spec/gap.md#711-cost-model) for the full derivation.

| Envelope | Scenario | Payload | % of Full | Payload savings | Apply Time |
|---|---|---:|---:|---:|---:|
| **synthesize** | Full generation (baseline) | 8,164 B | 100.0% | — | 1 ns |
| **edit** | 1 value replace (ID targeting) | 12 B | 0.1% | **99.9%** | 1.5 µs |
| **edit** | 4 value replaces (ID targeting) | 50 B | 0.6% | **99.4%** | 3.5 µs |
| **edit** | 1 section replace (ID targeting) | 441 B | 5.4% | **94.6%** | 1.4 µs |
| **edit** | 2 section replaces (ID targeting) | 516 B | 6.3% | **93.7%** | 3.8 µs |

## Limitations

1. **Conflict resolution** — GAP uses optimistic concurrency: the apply engine rejects edits whose version doesn't match `stored_version + 1`. Concurrent edits are rejected, not merged. There is no CRDT, OT, or automatic merge strategy — coordination is left to the orchestrator.

2. **Envelope generation** — The LLM must produce well-formed envelopes with correct target IDs, valid JSON structure, and appropriate operation types. In practice, generation can fail: malformed envelopes, hallucinated target IDs, or the model falling back to full regeneration when a targeted edit would suffice. The spec mitigates recall errors by passing a closed `targets` list in handles ([Section 7.2](spec/gap.md#72-handle-name-handle)), but reliable envelope production remains an active area of work.

3. **Granularity tradeoff** — Target placement affects generation reliability. Too coarse and edits replace large sections, losing efficiency. Too fine and the target set grows, increasing the chance of targeting errors and prompt complexity. When the system can't produce a valid envelope for a given granularity, it must fall back — and those fallback strategies need to be thought through.

4. **Adoption** — GAP requires tooling on both sides: producers must emit valid envelopes, consumers must implement the apply engine. The protocol is open and the spec is public, but the ecosystem is early.

## License

This project is dual-licensed:

- **Code** (`src/`, `apps/`, `benches/`, build files) — [Apache License 2.0](LICENSE)
- **Specification & docs** (`spec/`, `assets/`, documentation) — [CC-BY 4.0](LICENSE-CC-BY-4.0)

See [NOTICE](NOTICE) for details. Attribution is required under both licenses.
