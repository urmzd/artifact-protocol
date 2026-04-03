# AAP Evals

Evaluation framework for measuring the [Agent-Artifact Protocol](../spec/aap.md)'s token efficiency and envelope reliability claims against real LLM runs.

## What this tests

AAP's architecture is built on **context offloading** — the orchestrator never holds full artifact content. It provides a mechanism (tool calls, API, subprocess, etc.) through which artifact operations are dispatched to **ephemeral secondary contexts**. These contexts load the artifact, process an instruction, return a structured result (handle, projection, envelope), and terminate. The orchestrator is completely unaware of artifact content — it only sees what comes back through the mechanism it provided. This abstraction is what saves context.

Because the artifact is a concrete, standalone piece of content, it can also be interacted with directly — you can abandon the orchestrator context entirely and work with the artifact in a dedicated context for fine-tuning or manual refinement.

This architecture creates two independent dimensions of cost savings:

1. **Fewer output tokens** — the secondary context emits a diff envelope (~50-500 tokens) instead of regenerating the full artifact (~5,000-50,000 tokens)
2. **Cheaper compute for edits** — the maintain role (read existing content + produce structured diff) is a constrained task that doesn't require the same model capability as open-ended generation. Smaller, cheaper models with high recall and structured output suffice. The two effects multiply: fewer tokens × cheaper tokens.

The evals measure dimension 1 empirically. Dimension 2 is a deployment choice — but the evals establish *what* the maintain context needs to do (and how simple that task is), which informs model selection.

## How it works

Each experiment runs the **same sequence of edits** through two flows, starting from the same artifact:

**Default flow** — standard multi-turn conversation:
- Minimal system prompt + growing conversation history
- Each edit turn sends the full conversation so far + the edit instruction
- The model regenerates the entire artifact every time
- Context grows with every turn

**AAP flow** — stateless dispatch via context offloading:
- Each edit is an independent invocation of a maintain context
- Input: AAP system prompt (~350 tokens) + current artifact revision + edit instruction
- Output: JSON envelope (diff or section operations, ~50-500 tokens)
- The apply engine (Rust, ~2μs) resolves the envelope against the stored artifact
- Context is bounded and constant across turns

Both flows use the same model, temperature, seed, and edit instructions. The only independent variable is the conversation structure.

See [`data/experiments/EXPERIMENT.md`](data/experiments/EXPERIMENT.md) for full methodology, metrics schema, and fairness guarantees.

## Experiment coverage

88 experiments across 17 format categories:

| Format | Count | Examples |
|---|---|---|
| HTML | 15 | dashboards, landing pages, emails, forms, portfolios |
| Python | 12 | FastAPI, CLI tools, data pipelines, pytest suites |
| YAML | 11 | Kubernetes, Docker Compose, GitHub Actions, Ansible |
| JSON | 9 | Swagger/OpenAPI, package configs, GeoJSON |
| Markdown | 7 | blog posts, security policies, documentation |
| TypeScript | 4 | React components, form wizards |
| JavaScript | 4 | Express APIs, React data tables |
| SVG | 4 | charts, diagrams |
| Rust | 4 | CLI tools, HTTP handlers |
| Go | 4 | gRPC services, CLI tools |
| TOML | 3 | Cargo configs, pyproject files |
| Shell | 3 | build scripts, installers |
| CSS | 3 | design systems, themes |
| XML | 2 | Maven configs, Android layouts |
| SQL | 1 | migration scripts |
| Ruby | 1 | Rails models |
| Java | 1 | Spring controllers |

Each experiment has 3-4 edit turns with a mix of edit types: single value changes, row additions, style changes, and structural additions.

## Directory structure

```
evals/
├── data/experiments/
│   ├── EXPERIMENT.md              # full methodology and metrics schema
│   └── {NNN}-{format}-{name}/
│       ├── README.md              # experiment summary, expected sections, turns
│       ├── inputs/
│       │   ├── base/
│       │   │   ├── system.md      # default flow system prompt
│       │   │   ├── turn-0.md      # creation prompt (shared)
│       │   │   ├── turn-1.md      # edit instruction
│       │   │   └── ...
│       │   └── aap/
│       │       ├── init-system.md     # init context system prompt
│       │       └── maintain-system.md # maintain context system prompt
│       └── outputs/               # generated artifacts and envelopes
├── src/aap_evals/                 # evaluation harness
│   ├── cli.py                     # typer CLI entry point
│   ├── apply.py                   # apply engine bindings (Rust FFI)
│   ├── envelopes.py               # envelope parsing and validation
│   ├── markers.py                 # section marker utilities
│   ├── ollama.py                  # Ollama LLM client
│   └── _engine.cpython-*.so       # compiled Rust apply engine
└── pyproject.toml                 # maturin build (Rust FFI + Python)
```

## Running

Requires [Ollama](https://ollama.ai/) running locally and [uv](https://github.com/astral-sh/uv).

```bash
# Install dependencies (builds Rust FFI via maturin)
uv sync --project evals

# Run a single experiment
uv run --project evals aap-evals bench --experiment 1

# Run all experiments
uv run --project evals aap-evals bench

# Specify a different model
uv run --project evals aap-evals bench --model qwen3.5:9b
```

## What success looks like

- Output token savings >90% on edit turns
- Input tokens flat across turns (AAP) vs growing (default)
- Break-even at turn 1 or 2
- Envelope parse rate >80%
- Apply success rate >70%

See [EXPERIMENT.md](data/experiments/EXPERIMENT.md#interpreting-results) for detailed interpretation guidance.
