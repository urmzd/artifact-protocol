# Experiment: ts-api-client

**Format:** text/typescript | **Size:** medium | **Edits:** 3

**Expected sections:** types, client-class, endpoints, interceptors

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| GAP init system | 232 | 58 |
| GAP maintain system | 385 | 96 |
| **Protocol overhead** | | **~130 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'Milestone' type with fields: id, title, due_date, status, progress... |
| 2 | Rewrite the interceptors section to add a request deduplication interceptor t... |
| 3 | Add batch endpoint methods: batchUpdateTasks(updates: Array<{id: string, stat... |