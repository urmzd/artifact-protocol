# Experiment: shell-git-hooks

**Format:** text/x-sh | **Size:** tiny | **Edits:** 2

**Expected sections:** 

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
| 1 | Add a check that prevents commits containing TODO or FIXME comments unless th... |
| 2 | Update the secrets detection to also scan for AWS access keys matching the pa... |