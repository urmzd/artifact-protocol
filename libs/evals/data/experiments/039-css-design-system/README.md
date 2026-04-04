# Experiment: css-design-system

**Format:** text/css | **Size:** large | **Edits:** 4

**Expected sections:** variables, reset, typography, layout, components, utilities

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 89 | 22 |
| GAP init system | 225 | 56 |
| GAP maintain system | 378 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Change the primary color from blue to indigo (#4f46e5) and update the seconda... |
| 2 | Add a new 'breadcrumbs' component with separator chevrons, active state styli... |
| 3 | Rewrite the buttons component section to add a new 'danger' button variant wi... |
| 4 | Add a dark mode section using @media (prefers-color-scheme: dark) that invert... |