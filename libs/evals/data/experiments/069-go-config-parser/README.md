# Experiment: go-config-parser

**Format:** text/x-go | **Size:** small | **Edits:** 2

**Expected sections:** types, loader, validation

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| GAP init system | 226 | 56 |
| GAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'SMTP' sub-config to the types section with fields: host, port, use... |
| 2 | Update the validation to add a custom validator that checks the database DSN ... |