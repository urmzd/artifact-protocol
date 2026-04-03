# Experiment: yaml-docker-compose-microservices

**Format:** text/x-yaml | **Size:** medium | **Edits:** 4

**Expected sections:** services, networks, volumes

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
| 1 | Add a new 'monitoring' service using Prometheus with a scrape config targetin... |
| 2 | Update the PostgreSQL service to use version 16 and add a health check that r... |
| 3 | Add resource limits (CPU and memory) to every service: API gateway 0.5 CPU / ... |
| 4 | Add a new 'celery-worker' service that shares the same image as the notificat... |
