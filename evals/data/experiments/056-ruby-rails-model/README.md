# Experiment: ruby-rails-model

**Format:** text/x-ruby | **Size:** small | **Edits:** 2

**Expected sections:** associations, validations, scopes, methods

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
| 1 | Add a new 'has_many :refunds' association and a 'refund!' method that creates... |
| 2 | Update the scopes section to add a 'by_payment_method' scope that accepts :cr... |