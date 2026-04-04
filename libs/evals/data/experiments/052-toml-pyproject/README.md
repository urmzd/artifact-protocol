# Experiment: toml-pyproject

**Format:** text/x-toml | **Size:** small | **Edits:** 2

**Expected sections:** project, tools, build

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| GAP init system | 228 | 57 |
| GAP maintain system | 381 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add polars and pyarrow to the dependencies and create a new optional dependen... |
| 2 | Update the ruff configuration to add the 'I' (isort) and 'UP' (pyupgrade) rul... |