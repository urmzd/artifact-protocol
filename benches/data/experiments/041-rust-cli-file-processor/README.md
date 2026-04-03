# Experiment: rust-cli-file-processor

**Format:** text/x-rust | **Size:** medium | **Edits:** 3

**Expected sections:** cli, processor, output, tests

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
| 1 | Add a new --head flag to the CLI that shows only the first N rows of output, ... |
| 2 | Rewrite the output section to add a Markdown table formatter that generates G... |
| 3 | Add a new aggregation mode 'distinct' that counts unique values in a specifie... |
