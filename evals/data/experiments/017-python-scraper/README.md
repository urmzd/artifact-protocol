# Experiment: python-scraper

**Format:** text/x-python | **Size:** small | **Edits:** 2

**Expected sections:** config, fetcher, parser, storage

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
| 1 | Update the config to set the rate limit to 2 requests per second and add a pr... |
| 2 | Add a new parser field for 'discount_price' that extracts sale prices and cal... |