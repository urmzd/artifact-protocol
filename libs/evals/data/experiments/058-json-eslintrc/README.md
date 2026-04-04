# Experiment: json-eslintrc

**Format:** application/json | **Size:** tiny | **Edits:** 2

**Expected sections:** 

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 97 | 24 |
| GAP init system | 193 | 48 |
| GAP maintain system | 386 | 96 |
| **Protocol overhead** | | **~120 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add the 'react-hooks/exhaustive-deps' rule set to 'warn' and add 'plugin:@tan... |
| 2 | Change the parser from @typescript-eslint/parser to @babel/eslint-parser and ... |