# Experiment: js-react-data-table

**Format:** text/javascript | **Size:** medium | **Edits:** 4

**Expected sections:** hooks, columns, toolbar, table-body, pagination

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| GAP init system | 232 | 58 |
| GAP maintain system | 385 | 96 |
| **Protocol overhead** | | **~130 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'department' column after 'role' with values like Engineering, Mark... |
| 2 | Rewrite the toolbar component to include a date range filter with 'from' and ... |
| 3 | Add 10 more user entries to the sample data with international names and emai... |
| 4 | Update the pagination component to show 'Showing X-Y of Z results' text and a... |