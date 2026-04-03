# Experiment: svg-architecture-diagram

**Format:** image/svg+xml | **Size:** medium | **Edits:** 3

**Expected sections:** frontend, backend, data-layer, connections

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
| 1 | Add a new 'Monitoring' tier in purple with Prometheus, Grafana, and Jaeger bo... |
| 2 | Rewrite the backend tier to add a 'Search Service' box connected to an Elasti... |
| 3 | Update all connection arrows between API Gateway and backend services to show... |