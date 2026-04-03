# Experiment: go-worker-pool

**Format:** text/x-go | **Size:** small | **Edits:** 2

**Expected sections:** types, pool, workers, example

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
| 1 | Add a 'Priority' field to the Job interface and update the pool to process hi... |
| 2 | Update the example to process a batch of 20 image resize operations instead o... |
