# Experiment: json-i18n-translations

**Format:** application/json | **Size:** medium | **Edits:** 3

**Expected sections:** 

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
| 1 | Add a new 'teams' section with translation keys for team list, team detail, i... |
| 2 | Update all error messages in the 'common.errors' section to be more user-frie... |
| 3 | Add a 'notifications' section with keys for email, push, and in-app notificat... |