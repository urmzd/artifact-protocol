# Experiment: ts-state-store

**Format:** text/typescript | **Size:** small | **Edits:** 2

**Expected sections:** types, actions, reducers, selectors

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 239 | 59 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~250 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'applyBulkDiscount' action that applies a 15% discount when the car... |
| 2 | Update the getTaxAmount selector to accept a state tax rate parameter instead... |
