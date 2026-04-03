# Experiment: json-openapi-spec

**Format:** application/json | **Size:** large | **Edits:** 4

**Expected sections:** paths, schemas, responses

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 97 | 24 |
| AAP init system | 250 | 62 |
| AAP maintain system | 860 | 215 |
| **Protocol overhead** | | **~253 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new /wishlist endpoint group with POST /wishlist (add item), GET /wishl... |
| 2 | Update the Book schema to include a 'format' enum field with values 'hardcove... |
| 3 | Add rate limiting information to the API info section: 100 requests per minut... |
| 4 | Add a new /search endpoint that accepts query, category, price_min, price_max... |
