# Experiment: yaml-github-actions-release

**Format:** text/x-yaml | **Size:** medium | **Edits:** 3

**Expected sections:** triggers, build-matrix, publish, notifications

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 231 | 57 |
| AAP maintain system | 855 | 213 |
| **Protocol overhead** | | **~248 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a 'checksum' step after the build that generates SHA256 checksums for all... |
| 2 | Update the build matrix to add a musl target for Linux x86_64 that produces a... |
| 3 | Rewrite the notifications section to also send a Discord webhook notification... |
