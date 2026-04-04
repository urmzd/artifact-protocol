# Experiment: python-pytest-suite

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** fixtures, test-registration, test-login, test-permissions

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| GAP init system | 230 | 57 |
| GAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new fixture 'sample_superadmin' with elevated permissions and update th... |
| 2 | Add 3 new parametrized test cases to test-login for multi-factor authenticati... |
| 3 | Rewrite the test-registration section to include tests for OAuth signup via G... |