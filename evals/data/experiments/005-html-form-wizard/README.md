# Experiment: html-form-wizard

**Format:** text/html | **Size:** medium | **Edits:** 3

**Expected sections:** progress-bar, step-personal, step-address, step-payment, step-review

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 226 | 56 |
| AAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new Step 5 for 'Preferences' with fields for newsletter opt-in, preferr... |
| 2 | Update the progress bar to show 5 steps instead of 4 and change its color fro... |
| 3 | Rewrite Step 3 (Payment) to include PayPal and Apple Pay options as radio but... |