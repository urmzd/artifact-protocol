# Experiment: shell-deploy-script

**Format:** text/x-sh | **Size:** medium | **Edits:** 3

**Expected sections:** config, checks, build, deploy, verify

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 229 | 57 |
| AAP maintain system | 853 | 213 |
| **Protocol overhead** | | **~248 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a '--dry-run' flag to the script that prints every command without execut... |
| 2 | Rewrite the deploy section to support deploying to multiple servers defined i... |
| 3 | Add a rollback function that restores the previous symlink and restarts PM2 i... |
