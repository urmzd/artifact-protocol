# Experiment: js-utility-library

**Format:** text/javascript | **Size:** medium | **Edits:** 3

**Expected sections:** string-utils, date-utils, array-utils, validation-utils

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 239 | 59 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~250 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add three new string utilities: maskEmail (show first 2 chars + ***@domain), ... |
| 2 | Rewrite the date-utils section to add a formatDuration function that converts... |
| 3 | Add a new 'object-utils' section with functions: deepClone, deepMerge, pick, ... |
