# Experiment: go-grpc-service

**Format:** text/x-go | **Size:** medium | **Edits:** 3

**Expected sections:** types, service, handlers, interceptors

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 226 | 56 |
| AAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'ScheduleNotification' handler that accepts a delivery time and que... |
| 2 | Update the Types section to add a 'NotificationPriority' enum with values: LO... |
| 3 | Rewrite the interceptors to add a metrics interceptor that tracks request cou... |