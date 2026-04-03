# Experiment: toml-pyproject

**Format:** text/x-toml | **Size:** small | **Edits:** 2

**Expected sections:** project, tools, build

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 245 | 61 |
| AAP maintain system | 855 | 213 |
| **Protocol overhead** | | **~252 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add polars and pyarrow to the dependencies and create a new optional dependen... |
| 2 | Update the ruff configuration to add the 'I' (isort) and 'UP' (pyupgrade) rul... |
