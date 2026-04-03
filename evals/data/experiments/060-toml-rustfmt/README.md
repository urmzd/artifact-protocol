# Experiment: toml-rustfmt

**Format:** text/x-toml | **Size:** tiny | **Edits:** 2

**Expected sections:** 

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
| 1 | Change max_width to 120 and add wrap_comments = true and format_code_in_doc_c... |
| 2 | Add group_imports = 'StdExternalCrate' and reorder_imports = true settings |