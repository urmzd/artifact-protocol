# Experiment: json-swagger-pets

**Format:** application/json | **Size:** medium | **Edits:** 3

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
| 1 | Add a new /pets/{id}/medical-records endpoint group with GET (list records) a... |
| 2 | Update the Pet schema to add 'vaccinated', 'neutered', and 'microchipped' boo... |
| 3 | Add pagination parameters (page, per_page, sort_by) to all list endpoints and... |