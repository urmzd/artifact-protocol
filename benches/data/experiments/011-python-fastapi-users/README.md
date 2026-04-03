# Experiment: python-fastapi-users

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** models, schemas, crud, routes

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 233 | 58 |
| AAP maintain system | 857 | 214 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a 'role' field to UserCreate schema with allowed values 'admin', 'editor'... |
| 2 | Rewrite the list_users CRUD function to support filtering by role and is_acti... |
| 3 | Add a new PATCH /users/{id}/deactivate endpoint that sets is_active to False ... |
