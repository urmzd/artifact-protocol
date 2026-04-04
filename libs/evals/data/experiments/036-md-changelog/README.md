# Experiment: md-changelog

**Format:** text/markdown | **Size:** medium | **Edits:** 3

**Expected sections:** unreleased, v2, v1

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
| 1 | Add a new v2.4.0 release at the top of the v2 section with 3 Added items abou... |
| 2 | Update the unreleased section to include a Deprecated entry for the legacy XM... |
| 3 | Rewrite the v1.0.0 entry to expand it with a detailed 'Migration Guide from v... |