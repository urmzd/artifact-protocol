# Experiment: python-pytest-suite

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** fixtures, test-registration, test-login, test-permissions

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| AAP init system | 233 | 58 |
| AAP maintain system | 857 | 214 |
| **Protocol overhead** | | **~249 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new fixture 'sample_superadmin' with elevated permissions and update th... |
| 2 | Add 3 new parametrized test cases to test-login for multi-factor authenticati... |
| 3 | Rewrite the test-registration section to include tests for OAuth signup via G... |
