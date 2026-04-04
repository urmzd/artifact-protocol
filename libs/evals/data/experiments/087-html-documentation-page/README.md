# Experiment: html-documentation-page

**Format:** text/html | **Size:** large | **Edits:** 4

**Expected sections:** sidebar, content, code-examples, api-reference

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
| 1 | Rewrite the sidebar navigation to add a 'Plugins' section with 3 sub-items: O... |
| 2 | Add 3 more functions to the API reference: 'pipe', 'compose', and 'memoize' w... |
| 3 | Update the installation section to add a Deno import example and a 'Requireme... |
| 4 | Add a 'Migration Guide' section after the FAQ showing how to migrate from v1 ... |