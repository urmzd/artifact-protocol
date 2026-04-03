# Experiment: yaml-renovate

**Format:** text/x-yaml | **Size:** tiny | **Edits:** 2

**Expected sections:** 

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 231 | 57 |
| AAP maintain system | 855 | 213 |
| **Protocol overhead** | | **~248 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a packageRule that groups all @types/* packages into a single PR with aut... |
| 2 | Update the schedule to run only on weekends and add a 'prConcurrentLimit' of 5 |
