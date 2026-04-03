# Experiment: md-api-docs

**Format:** text/markdown | **Size:** large | **Edits:** 4

**Expected sections:** authentication, users-endpoints, projects-endpoints, errors, rate-limiting

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 230 | 57 |
| AAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'Teams' endpoint group after Projects with CRUD operations for team... |
| 2 | Update the errors section to add 5 new error codes: 409 Conflict, 413 Payload... |
| 3 | Rewrite the authentication section to add a new 'Service Account' authenticat... |
| 4 | Add webhook documentation showing available events (project.created, task.upd... |