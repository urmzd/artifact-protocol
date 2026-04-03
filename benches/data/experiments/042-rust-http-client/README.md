# Experiment: rust-http-client

**Format:** text/x-rust | **Size:** medium | **Edits:** 3

**Expected sections:** types, client, endpoints, error

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 235 | 58 |
| AAP maintain system | 855 | 213 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'air_quality' endpoint method that takes a Location and returns an ... |
| 2 | Update the error type to add a 'Timeout' variant and implement a retry_with_b... |
| 3 | Add a caching layer to the client that stores responses in a HashMap with TTL... |
