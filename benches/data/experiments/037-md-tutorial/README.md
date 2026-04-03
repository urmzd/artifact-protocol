# Experiment: md-tutorial

**Format:** text/markdown | **Size:** medium | **Edits:** 3

**Expected sections:** intro, setup, building, testing, deploying

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 247 | 61 |
| AAP maintain system | 857 | 214 |
| **Protocol overhead** | | **~252 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Update the setup section to use uv instead of pip for dependency management, ... |
| 2 | Add a new 'Monitoring' subsection to the deploying section covering Prometheu... |
| 3 | Rewrite the testing section to add a 'Load Testing' subsection using locust w... |
