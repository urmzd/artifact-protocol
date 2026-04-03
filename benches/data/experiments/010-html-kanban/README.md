# Experiment: html-kanban

**Format:** text/html | **Size:** medium | **Edits:** 4

**Expected sections:** board-header, col-backlog, col-in-progress, col-review, col-done

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
| 1 | Change the project name from 'Sprint 24' to 'Sprint 27 — Q2 Launch' and upd... |
| 2 | Move 2 cards from Backlog to In Progress and add a 'Blocked' label to the fir... |
| 3 | Add a new 'Cancelled' column after Done with 2 cancelled task cards |
| 4 | Change all 'critical' priority tags to have a red pulsing animation effect |
