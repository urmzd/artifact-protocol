# Experiment: json-package-monorepo

**Format:** application/json | **Size:** small | **Edits:** 2

**Expected sections:** 

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 97 | 24 |
| AAP init system | 193 | 48 |
| AAP maintain system | 386 | 96 |
| **Protocol overhead** | | **~120 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add drizzle-orm and @auth/core to the dependencies with realistic version num... |
| 2 | Update the scripts section to add 'db:migrate', 'db:seed', and 'db:studio' co... |