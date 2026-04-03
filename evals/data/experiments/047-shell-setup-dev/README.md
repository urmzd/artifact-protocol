# Experiment: shell-setup-dev

**Format:** text/x-sh | **Size:** small | **Edits:** 2

**Expected sections:** detect-os, install-deps, configure, verify

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 226 | 56 |
| AAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add Rust installation via rustup to the install-deps section with the stable ... |
| 2 | Update the verify section to output a formatted summary table showing each to... |