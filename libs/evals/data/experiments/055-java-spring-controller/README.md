# Experiment: java-spring-controller

**Format:** text/x-java | **Size:** medium | **Edits:** 3

**Expected sections:** imports, controller, service, repository

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| GAP init system | 228 | 57 |
| GAP maintain system | 381 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new GET /products/export endpoint in the controller that returns produc... |
| 2 | Update the ProductService to add a bulkUpdatePrices method that accepts a Map... |
| 3 | Rewrite the repository to add a custom @Query method findByPriceRangeAndCateg... |