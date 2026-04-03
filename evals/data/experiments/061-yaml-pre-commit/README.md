# Experiment: yaml-pre-commit

**Format:** text/x-yaml | **Size:** tiny | **Edits:** 2

**Expected sections:** 

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 228 | 57 |
| AAP maintain system | 381 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a bandit hook for security linting with a severity level of medium and a ... |
| 2 | Update the ruff hook to pin version 0.9.0 and add the --fix flag to automatic... |