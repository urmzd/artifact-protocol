# Experiment: sql-schema-ecommerce

**Format:** text/x-sql | **Size:** medium | **Edits:** 3

**Expected sections:** tables, indexes, views, seed-data

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 91 | 22 |
| AAP init system | 227 | 56 |
| AAP maintain system | 380 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'wishlists' table with columns: id, user_id (FK), product_id (FK), ... |
| 2 | Rewrite the seed-data section to add 10 more products across all categories w... |
| 3 | Add a new materialized view 'monthly_sales_summary' that aggregates total rev... |