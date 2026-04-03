# Experiment: yaml-terraform-vars

**Format:** text/x-yaml | **Size:** small | **Edits:** 2

**Expected sections:** environment, networking, compute

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 92 | 23 |
| AAP init system | 231 | 57 |
| AAP maintain system | 855 | 213 |
| **Protocol overhead** | | **~248 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Update the environment name to 'production', region to 'us-west-2', and add a... |
| 2 | Change the compute instance type to 'c6g.xlarge' (ARM-based) and update the A... |
