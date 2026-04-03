# Experiment: json-tsconfig

**Format:** application/json | **Size:** tiny | **Edits:** 2

**Expected sections:** 

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 97 | 24 |
| AAP init system | 250 | 62 |
| AAP maintain system | 860 | 215 |
| **Protocol overhead** | | **~253 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add path aliases for '@/components/*', '@/lib/*', and '@/hooks/*' pointing to... |
| 2 | Change the target from ES2017 to ES2022 and enable the 'decorators' and 'verb... |
