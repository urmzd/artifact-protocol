# Experiment: python-celery-tasks

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** config, email-tasks, report-tasks, cleanup-tasks

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
| 1 | Add a new 'send_invoice_email' task to the email-tasks section that accepts o... |
| 2 | Update the config to use a dead letter queue named 'failed_tasks' and set the... |
| 3 | Rewrite the cleanup-tasks section to add a new 'rotate_logs' task that compre... |