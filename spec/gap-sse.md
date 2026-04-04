# GAP-SSE: Server-Sent Events Transport Binding

**Version**: 0.1
**Status**: Draft — subject to breaking changes
**Date**: 2026-04-03
**Companion to**: [Generative Artifact Protocol (GAP)](gap.md)

---

## 1. Overview

This document defines a normative Server-Sent Events (SSE) wire format for streaming GAP envelopes over HTTP. Implementations claiming SSE transport support MUST conform to this specification.

SSE is a natural fit for GAP's unidirectional model — the producer streams envelope content to the consumer over a long-lived HTTP connection. Since GAP envelopes are complete JSON messages, SSE serves as a delivery mechanism rather than a chunking layer — each event carries a self-contained envelope or control signal.

---

## 2. Event Types

| SSE `event:` value | Payload (`data:`) | Purpose |
|---|---|---|
| `gap:envelope` | JSON-encoded GAP envelope (any `name`: `synthesize`, `edit`, or `handle`) | Deliver a complete envelope |
| `gap:error` | JSON-encoded error object (see [Section 5](#5-error-signaling)) | Error signaling |
| `gap:heartbeat` | `{}` | Keep-alive during idle periods |
| `gap:complete` | JSON object with optional `tokens_used` and `checksum` | Stream completion |

The `gap:` prefix namespaces events to avoid collisions when multiplexing or sharing an SSE endpoint.

---

## 3. Event ID and Reconnection

The SSE `id:` field on every `gap:envelope` event MUST be set to a monotonically increasing sequence number (as a string). This enables the standard SSE `Last-Event-ID` reconnection mechanism.

On reconnection:

1. The client sends `Last-Event-ID: <seq>` in the HTTP request
2. The server resumes from `seq + 1`
3. If the requested seq is no longer available, the server MUST send an `gap:error` event with code `"seq_expired"` and the client MUST restart the stream
4. On reconnection, the server MAY omit previously delivered `gap:envelope` events

**Default retry interval:**

```
retry: 3000
```

The server SHOULD set `retry:` on the first event. The server MAY increase the interval on repeated reconnections (exponential backoff).

---

## 4. Wire Format

### 4.1 Connection Open — Synthesize Envelope

```
retry: 3000

event: gap:envelope
id: 0
data: {"protocol":"gap/0.1","id":"dashboard-001","version":1,"name":"synthesize","meta":{"format":"text/html"},"content":[{"body":"<!DOCTYPE html><html><body><gap:target id=\"stats\"><h1>Revenue: $12,340</h1></gap:target></body></html>"}]}

```

### 4.2 Edit Envelope

```
event: gap:envelope
id: 1
data: {"protocol":"gap/0.1","id":"dashboard-001","version":2,"name":"edit","meta":{"format":"text/html"},"content":[{"op":"replace","target":{"type":"id","value":"stats"},"content":"<h1>Revenue: $15,720</h1>"}]}

```

### 4.3 Handle Envelope

```
event: gap:envelope
id: 2
data: {"protocol":"gap/0.1","id":"dashboard-001","version":2,"name":"handle","meta":{"format":"text/html","tokens_used":42},"content":[]}

```

### 4.4 Completion

```
event: gap:complete
data: {"tokens_used":847,"checksum":"sha256:abc123def456..."}

```

### 4.5 Heartbeat

Sent at regular intervals when no envelopes are in transit:

```
event: gap:heartbeat
data: {}

```

### 4.6 Error

```
event: gap:error
data: {"code":"version_conflict","message":"Expected base version 2, got 1","fatal":true}

```

---

## 5. Error Signaling

Errors mid-stream are delivered as `gap:error` events. The stream MAY continue after a non-fatal error or MUST close after a fatal one.

### 5.1 Error Object

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | string | YES | Machine-readable error code |
| `message` | string | YES | Human-readable description |
| `fatal` | boolean | no | If `true`, the stream terminates. Default: `false` |
| `artifact_id` | string | no | Artifact that triggered the error (useful when multiplexing) |

### 5.2 Error Codes

| Code | Fatal | Description |
|---|---|---|
| `seq_expired` | YES | Requested `Last-Event-ID` is no longer available |
| `budget_exceeded` | YES | Token budget exhausted before generation completed |
| `version_conflict` | YES | Version mismatch detected — edit targets a stale version |
| `target_not_found` | no | A referenced `<gap:target>` ID or JSON Pointer does not exist |
| `timeout` | YES | Generation timed out |
| `internal` | YES | Unspecified server error |

---

## 6. Connection Lifecycle

1. **Open**: Client issues `GET` with `Accept: text/event-stream`
2. **Envelope(s)**: Server sends one or more `gap:envelope` events (any `name` type)
3. **Heartbeat**: Server sends `gap:heartbeat` at regular intervals (RECOMMENDED: every 15 seconds) during idle periods
4. **Completion**: Server sends `gap:complete`
5. **Close**: Server closes the connection. Client SHOULD NOT auto-reconnect after `gap:complete`

**HTTP headers:**

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

---

## 7. Multiplexing

A single SSE connection MAY carry envelopes for multiple artifacts. When multiplexing:

- Each `gap:envelope` event naturally carries its `id` field (the artifact identifier) within the envelope payload
- The SSE `id:` field uses the format `<artifact_id>:<seq>` to distinguish reconnection positions per artifact
- `gap:complete` and `gap:error` events MUST include `artifact_id`
- The connection closes only after all artifact streams are complete

**Example** (multiplexed envelopes):

```
event: gap:envelope
id: dashboard-001:0
data: {"protocol":"gap/0.1","id":"dashboard-001","version":1,"name":"synthesize","meta":{"format":"text/html"},"content":[{"body":"..."}]}

event: gap:envelope
id: sidebar-002:0
data: {"protocol":"gap/0.1","id":"sidebar-002","version":1,"name":"synthesize","meta":{"format":"text/html"},"content":[{"body":"..."}]}

event: gap:envelope
id: dashboard-001:1
data: {"protocol":"gap/0.1","id":"dashboard-001","version":2,"name":"edit","meta":{"format":"text/html"},"content":[{"op":"replace","target":{"type":"id","value":"revenue-value"},"content":"$15,720"}]}

```

---

## 8. Security Considerations

- SSE connections SHOULD use TLS (HTTPS)
- Authentication SHOULD be handled via standard HTTP mechanisms (Bearer tokens, cookies)
- Servers SHOULD set appropriate CORS headers when serving cross-origin clients
- The `retry` interval SHOULD NOT be set below 1000ms to prevent reconnection storms
