# Experiment: shell-deploy-script

**Format:** text/x-sh | **Size:** medium | **Edits:** 3

**Expected sections:** config, checks, build, deploy, verify

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| GAP init system | 226 | 56 |
| GAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a '--dry-run' flag to the script that prints every command without execut... |
| 2 | Rewrite the deploy section to support deploying to multiple servers defined i... |
| 3 | Add a rollback function that restores the previous symlink and restarts PM2 i... |