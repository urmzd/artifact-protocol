# Experiment: python-dataclasses-models

**Format:** text/x-python | **Size:** small | **Edits:** 2

**Expected sections:** base, entities, value-objects

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 233 | 58 |
| AAP maintain system | 857 | 214 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'Milestone' entity with fields: id, name, target_date, status, proj... |
| 2 | Update the Priority enum to include a 'URGENT' level above 'HIGH' and add a c... |
