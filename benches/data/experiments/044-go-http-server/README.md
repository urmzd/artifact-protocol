# Experiment: go-http-server

**Format:** text/x-go | **Size:** medium | **Edits:** 3

**Expected sections:** types, handlers, middleware, server

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 233 | 58 |
| AAP maintain system | 853 | 213 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new GetTopURLs handler (GET /urls/top?limit=10) that returns the most-c... |
| 2 | Update the rate limiting middleware to use a per-IP token bucket with configu... |
| 3 | Add URL expiration support: a new 'expires_at' field on the URL struct and a ... |
