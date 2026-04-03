# Experiment: python-fastapi-auth

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** config, jwt-utils, dependencies, routes

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
| 1 | Update the config section to change the access token expiry to 15 minutes and... |
| 2 | Add a new POST /auth/change-password route that requires the current password... |
| 3 | Rewrite the dependencies section to add an 'require_verified_email' dependenc... |
