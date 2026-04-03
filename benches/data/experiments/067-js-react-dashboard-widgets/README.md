# Experiment: js-react-dashboard-widgets

**Format:** text/javascript | **Size:** medium | **Edits:** 3

**Expected sections:** stat-card, chart-widget, activity-feed, quick-actions

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 239 | 59 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~250 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Update the StatCard component to accept a 'sparkline' prop with an array of 7... |
| 2 | Add 5 more activity items to the ActivityFeed showing deployment, code review... |
| 3 | Rewrite the QuickActions section to have 8 action buttons instead of 6, addin... |
