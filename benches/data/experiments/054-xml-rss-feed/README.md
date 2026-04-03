# Experiment: xml-rss-feed

**Format:** application/xml | **Size:** medium | **Edits:** 3

**Expected sections:** channel-info, items

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 249 | 62 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~253 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add 5 new items about Rust, WebAssembly, and edge computing topics with dates... |
| 2 | Update the channel-info to change the blog name to 'CodeStream Weekly' and ad... |
| 3 | Change the category of all AI/ML related items from 'Technology' to 'Artifici... |
