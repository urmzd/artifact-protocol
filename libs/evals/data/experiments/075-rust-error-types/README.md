# Experiment: rust-error-types

**Format:** text/x-rust | **Size:** small | **Edits:** 2

**Expected sections:** error-enum, display-impl, conversions

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
| 1 | Add a new 'Conflict' variant for HTTP 409 responses with a 'resource_id' fiel... |
| 2 | Update the From implementation for sqlx::Error to distinguish between unique ... |