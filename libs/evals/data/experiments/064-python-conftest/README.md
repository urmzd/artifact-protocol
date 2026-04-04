# Experiment: python-conftest

**Format:** text/x-python | **Size:** small | **Edits:** 2

**Expected sections:** fixtures, factories, helpers

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| GAP init system | 230 | 57 |
| GAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new fixture 'mock_redis' that patches the Redis connection with fakered... |
| 2 | Rewrite the factories section to add a 'create_comment' factory with fields: ... |