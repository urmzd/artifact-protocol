# Experiment: python-scraper

**Format:** text/x-python | **Size:** small | **Edits:** 2

**Expected sections:** config, fetcher, parser, storage

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
| 1 | Update the config to set the rate limit to 2 requests per second and add a pr... |
| 2 | Add a new parser field for 'discount_price' that extracts sale prices and cal... |
