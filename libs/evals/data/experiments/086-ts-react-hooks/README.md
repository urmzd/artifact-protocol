# Experiment: ts-react-hooks

**Format:** text/typescript | **Size:** medium | **Edits:** 3

**Expected sections:** data-hooks, ui-hooks, form-hooks

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| GAP init system | 232 | 58 |
| GAP maintain system | 385 | 96 |
| **Protocol overhead** | | **~130 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new useWebSocket<T> hook to the data-hooks section that manages a WebSo... |
| 2 | Update the useForm hook to support nested object fields using dot notation pa... |
| 3 | Rewrite the useToast hook to support toast stacking with a max of 5 visible t... |