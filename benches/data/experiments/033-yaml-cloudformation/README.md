# Experiment: yaml-cloudformation

**Format:** text/x-yaml | **Size:** large | **Edits:** 4

**Expected sections:** parameters, vpc-resources, compute, database, outputs

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
| 1 | Add a new ElastiCache Redis cluster resource in a private subnet with 2 cache... |
| 2 | Update the Auto Scaling Group to use a target tracking scaling policy based o... |
| 3 | Add a new 'environment' parameter with allowed values 'dev', 'staging', 'prod... |
| 4 | Add an S3 bucket resource for static assets with CloudFront distribution and ... |
