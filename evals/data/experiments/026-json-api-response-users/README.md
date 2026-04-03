# Experiment: json-api-response-users

**Format:** application/json | **Size:** medium | **Edits:** 3

**Expected sections:** meta, data, pagination

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 97 | 24 |
| AAP init system | 193 | 48 |
| AAP maintain system | 386 | 96 |
| **Protocol overhead** | | **~120 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add 10 more users to the data array with roles 'billing_admin' and 'support_a... |
| 2 | Update the pagination to show page 3 of 12 with per_page set to 30 and update... |
| 3 | Add a 'team_id' and 'team_name' field to each user object, with users grouped... |