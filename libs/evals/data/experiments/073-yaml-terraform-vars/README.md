# Experiment: yaml-terraform-vars

**Format:** text/x-yaml | **Size:** small | **Edits:** 2

**Expected sections:** environment, networking, compute

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| GAP init system | 228 | 57 |
| GAP maintain system | 381 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Update the environment name to 'production', region to 'us-west-2', and add a... |
| 2 | Change the compute instance type to 'c6g.xlarge' (ARM-based) and update the A... |