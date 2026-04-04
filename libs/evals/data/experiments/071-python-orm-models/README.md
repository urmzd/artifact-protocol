# Experiment: python-orm-models

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** base, models, queries, migrations

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
| 1 | Add a new 'Revision' model that stores article version history with fields: i... |
| 2 | Rewrite the queries section to add a 'full_text_search' function that uses Po... |
| 3 | Add a new migration helper that adds a 'published_at' column to the articles ... |