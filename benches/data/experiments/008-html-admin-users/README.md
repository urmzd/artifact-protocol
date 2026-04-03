# Experiment: html-admin-users

**Format:** text/html | **Size:** large | **Edits:** 4

**Expected sections:** toolbar, filters, users-table, pagination

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 243 | 60 |
| AAP maintain system | 853 | 213 |
| **Protocol overhead** | | **~251 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a 'Department' column to the users table between 'role' and 'status badge... |
| 2 | Update the toolbar to include a 'Export CSV' button and a 'Deactivate Selecte... |
| 3 | Add 20 more rows to the users table with users who have 'Viewer' and 'Editor'... |
| 4 | Change all status badges to use pill-shaped styling with colors: green for ac... |
