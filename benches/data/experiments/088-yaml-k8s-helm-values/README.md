# Experiment: yaml-k8s-helm-values

**Format:** text/x-yaml | **Size:** medium | **Edits:** 3

**Expected sections:** global, app, database, monitoring

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
| 1 | Update the app section to set replicas to 5, change the image tag to 'v2.4.0'... |
| 2 | Add a new 'redis' section after database with architecture set to 'replicatio... |
| 3 | Rewrite the monitoring section to add custom Grafana dashboard JSON for reque... |
