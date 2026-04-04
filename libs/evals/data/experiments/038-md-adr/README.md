# Experiment: md-adr

**Format:** text/markdown | **Size:** small | **Edits:** 2

**Expected sections:** context, decision, consequences

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| GAP init system | 230 | 57 |
| GAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Update the status from 'Accepted' to 'Superseded by ADR-007' and add a link r... |
| 2 | Add a third alternative considered: 'Use CDC (Change Data Capture) with Debez... |