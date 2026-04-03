# Experiment: html-invoice

**Format:** text/html | **Size:** small | **Edits:** 2

**Expected sections:** header, addresses, line-items, totals

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
| 1 | Change the company name to 'NovaTech Industries' and invoice number to INV-20... |
| 2 | Add 4 more line items: Cloud Hosting Setup ($2,400), SSL Certificate ($199), ... |