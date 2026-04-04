# Experiment: yaml-k8s-deployment

**Format:** text/x-yaml | **Size:** medium | **Edits:** 3

**Expected sections:** deployment, service, ingress, hpa, configmap

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
| 1 | Update the Deployment to use 5 replicas and add a PodDisruptionBudget with mi... |
| 2 | Add a new Secret manifest containing database credentials and update the Depl... |
| 3 | Rewrite the Ingress to add a second host rule for api.example.com routing to ... |