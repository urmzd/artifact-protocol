# Experiment: yaml-renovate

**Format:** text/x-yaml | **Size:** tiny | **Edits:** 2

**Expected sections:** 

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
| 1 | Add a packageRule that groups all @types/* packages into a single PR with aut... |
| 2 | Update the schedule to run only on weekends and add a 'prConcurrentLimit' of 5 |