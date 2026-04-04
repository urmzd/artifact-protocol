# Experiment: html-email-receipt

**Format:** text/html | **Size:** small | **Edits:** 2

**Expected sections:** header, order-summary, items, totals

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| GAP init system | 226 | 56 |
| GAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Change the order number to ORD-2026-03-4821 and the date to March 28, 2026 |
| 2 | Add 3 more products to the items table: Wireless Charger ($34.99, qty 1), USB... |