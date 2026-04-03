---
name: generate-artifact
description: "Generate a single benchmark artifact using Ollama. Produces a realistic LLM-generated file (HTML, Python, JS, JSON, YAML, etc.) with AAP section markers, stored in the standard NNN-label/ directory structure."
---

# generate-artifact

Generate a single benchmark artifact for the AAP corpus using a local LLM via Ollama.

## Usage

```bash
# Generate artifact #42
just generate-artifact n=42

# Generate with a specific model
just generate-artifact n=42 model=qwen3.5:9b

# Generate directly via the script
uv run --project tools ag-generate-corpus --single 42
uv run --project tools ag-generate-corpus --single 42 --model gemma3 --force
```

## Output Structure

Each artifact is stored in `assets/inputs/NNN-label/`:

```
assets/inputs/042-label/
├── prompt.md           # The prompt sent to the LLM (human-readable)
├── instructions.json   # Structured metadata (format, model, sections, checksum)
└── artifacts/
    └── users_api.py    # The LLM-generated artifact file
```

## Prompt Catalog

The generator cycles through ~70 prompt templates covering:

- **HTML**: dashboards, landing pages, email templates, forms, status pages, kanban boards
- **Python**: FastAPI, CLI tools, data pipelines, test suites, ORM models, middleware
- **JavaScript/TypeScript**: React components, Express APIs, utility libraries, state stores, hooks
- **JSON**: OpenAPI specs, package.json, API responses, i18n, seed data, configs
- **YAML**: docker-compose, GitHub Actions, Kubernetes, Ansible, CloudFormation, Helm
- **Markdown**: README, API docs, changelog, tutorials, ADRs, CONTRIBUTING
- **CSS**: design systems, animations, responsive grids
- **Rust**: CLI tools, HTTP clients, data structures, error handling
- **Go**: HTTP servers, worker pools, config parsers, gRPC services
- **Shell**: deploy scripts, dev setup, git hooks
- **SVG**: bar charts, pie charts, architecture diagrams, icon sprites
- **TOML/XML/SQL**: Cargo.toml, pyproject.toml, Maven POM, RSS feeds, database schemas

Each prompt includes instructions for AAP section markers appropriate to the format.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `qwen3.5:4b` | Ollama model to use |
| `--single N` | — | Generate just artifact N |
| `--count N` | `1000` | Number of artifacts (batch mode) |
| `--output DIR` | `assets/inputs` | Output directory |
| `--force` | — | Regenerate even if exists |
