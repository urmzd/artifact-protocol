# Experiment: md-readme-cli

**Format:** text/markdown | **Size:** medium | **Edits:** 3

**Expected sections:** overview, installation, usage, configuration, api

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 230 | 57 |
| AAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'Troubleshooting' section after API with 5 common issues and their ... |
| 2 | Update the usage section to add examples for two new commands: 'dbmigrate squ... |
| 3 | Rewrite the installation section to add Docker installation instructions with... |