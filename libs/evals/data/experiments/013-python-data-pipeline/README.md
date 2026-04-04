# Experiment: python-data-pipeline

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** extraction, transformation, validation, loading

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
| 1 | Add a new transformation step that calculates a 'customer_lifetime_value' met... |
| 2 | Update the validation section to add a check that rejects rows where the sale... |
| 3 | Rewrite the loading section to also output a summary CSV with one row per reg... |