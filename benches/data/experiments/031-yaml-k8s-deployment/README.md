# Experiment: yaml-k8s-deployment

**Format:** text/x-yaml | **Size:** medium | **Edits:** 3

**Expected sections:** deployment, service, ingress, hpa, configmap

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
| 1 | Update the Deployment to use 5 replicas and add a PodDisruptionBudget with mi... |
| 2 | Add a new Secret manifest containing database credentials and update the Depl... |
| 3 | Rewrite the Ingress to add a second host rule for api.example.com routing to ... |
