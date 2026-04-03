# Experiment: go-config-parser

**Format:** text/x-go | **Size:** small | **Edits:** 2

**Expected sections:** types, loader, validation

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 233 | 58 |
| AAP maintain system | 853 | 213 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'SMTP' sub-config to the types section with fields: host, port, use... |
| 2 | Update the validation to add a custom validator that checks the database DSN ... |
