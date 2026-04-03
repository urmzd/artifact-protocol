# Experiment: js-express-api

**Format:** text/javascript | **Size:** medium | **Edits:** 3

**Expected sections:** middleware, models, routes, error-handling

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
| 1 | Add a new 'labels' field to the Task model with an array of strings, and add ... |
| 2 | Rewrite the auth token verification middleware to support both Bearer tokens ... |
| 3 | Add a new route POST /projects/:id/archive that marks a project as archived a... |
