# Experiment: rust-data-structures

**Format:** text/x-rust | **Size:** medium | **Edits:** 3

**Expected sections:** lru-cache, trie, bloom-filter, tests

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 228 | 57 |
| AAP maintain system | 381 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a 'get_or_insert' method to the LRU Cache that takes a key and a closure,... |
| 2 | Rewrite the Trie to support wildcard matching where '?' matches any single ch... |
| 3 | Add a new 'count_prefix' method to the Trie that returns how many inserted wo... |