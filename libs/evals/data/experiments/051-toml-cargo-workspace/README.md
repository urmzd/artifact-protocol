# Experiment: toml-cargo-workspace

**Format:** text/x-toml | **Size:** small | **Edits:** 2

**Expected sections:** package, dependencies, workspace

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
| 1 | Add sqlx and sea-orm to the dependencies with features for PostgreSQL and run... |
| 2 | Update the release profile to enable codegen-units = 1 and add a bench profil... |