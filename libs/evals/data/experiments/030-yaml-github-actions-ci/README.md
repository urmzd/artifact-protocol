# Experiment: yaml-github-actions-ci

**Format:** text/x-yaml | **Size:** medium | **Edits:** 3

**Expected sections:** triggers, lint-job, test-job, build-job, deploy-job

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
| 1 | Add a new 'security-scan' job between lint and test that runs npm audit and S... |
| 2 | Update the deploy job to add a manual approval step before production deploym... |
| 3 | Rewrite the test job to also run Playwright e2e tests in a separate matrix en... |