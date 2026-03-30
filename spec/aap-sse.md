# AAP-SSE: Server-Sent Events Transport Binding

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-29
**Companion to**: [Agent-Artifact Protocol (AAP)](aap.md)

---

## 1. Overview

This document defines a normative Server-Sent Events (SSE) wire format for the AAP streaming protocol ([AAP Section 6](aap.md#6-streaming-protocol)). Implementations claiming SSE transport support MUST conform to this specification.

SSE is a natural fit for AAP's unidirectional streaming model — the producer streams artifact chunks to the consumer over a long-lived HTTP connection.

---

## 2. Event Types

| SSE `event:` value | Payload (`data:`) | Purpose |
|---|---|---|
| `aap:envelope` | JSON-encoded envelope metadata (all fields except content payloads) | Establishes artifact identity. Sent first |
| `aap:chunk` | JSON-encoded chunk frame ([AAP Section 6.1](aap.md#61-chunk-frame)) without the `envelope` field | Content delivery |
| `aap:error` | JSON-encoded error object (see [Section 5](#5-error-signaling)) | Error signaling |
| `aap:heartbeat` | `{}` | Keep-alive during idle periods |
| `aap:complete` | JSON object with optional `tokens_used` and `checksum` | Stream completion |

The `aap:` prefix namespaces events to avoid collisions when multiplexing or sharing an SSE endpoint.

---

## 3. Event ID and Reconnection

The SSE `id:` field on every `aap:chunk` event MUST be set to the chunk's `seq` value (as a string). This enables the standard SSE `Last-Event-ID` reconnection mechanism.

On reconnection:

1. The client sends `Last-Event-ID: <seq>` in the HTTP request
2. The server resumes from `seq + 1`
3. If the requested seq is no longer available, the server MUST send an `aap:error` event with code `"seq_expired"` and the client MUST restart the stream
4. On reconnection, the server MAY omit the `aap:envelope` event if `Last-Event-ID` is valid

**Default retry interval:**

```
retry: 3000
```

The server SHOULD set `retry:` on the first event. The server MAY increase the interval on repeated reconnections (exponential backoff).

---

## 4. Wire Format

### 4.1 Connection Open — Envelope

```
retry: 3000

event: aap:envelope
data: {"protocol":"aap/1.0","id":"dashboard-001","version":1,"format":"text/html","mode":"full","rendering":{"display":"preview"}}

```

### 4.2 Content Chunks

```
event: aap:chunk
id: 0
data: {"seq":0,"content":"<!DOCTYPE html><html>","flush":true}

event: aap:chunk
id: 1
data: {"seq":1,"content":"<head><title>Report</title></head>","flush":true}

event: aap:chunk
id: 2
data: {"seq":2,"content":"<body><h1>Q4 Report</h1>","flush":false}

event: aap:chunk
id: 3
data: {"seq":3,"content":"<p>Revenue up 15%.</p></body></html>","flush":true}

```

### 4.3 Completion

```
event: aap:complete
data: {"tokens_used":847,"checksum":"sha256:abc123def456..."}

```

### 4.4 Heartbeat

Sent at regular intervals when no chunks are in transit:

```
event: aap:heartbeat
data: {}

```

### 4.5 Error

```
event: aap:error
data: {"code":"section_failed","message":"Section 'orders' generation timed out","fatal":false,"seq":12}

```

---

## 5. Error Signaling

Errors mid-stream are delivered as `aap:error` events. The stream MAY continue after a non-fatal error or MUST close after a fatal one.

### 5.1 Error Object

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | string | YES | Machine-readable error code |
| `message` | string | YES | Human-readable description |
| `fatal` | boolean | no | If `true`, the stream terminates. Default: `false` |
| `seq` | integer | no | Sequence number of the chunk that triggered the error |

### 5.2 Error Codes

| Code | Fatal | Description |
|---|---|---|
| `seq_expired` | YES | Requested `Last-Event-ID` is no longer available |
| `budget_exceeded` | YES | Token budget exhausted before generation completed |
| `version_conflict` | YES | `base_version` mismatch detected during streaming |
| `section_failed` | no | A section generation failed; other sections may continue |
| `timeout` | YES | Generation timed out |
| `internal` | YES | Unspecified server error |

---

## 6. Connection Lifecycle

1. **Open**: Client issues `GET` with `Accept: text/event-stream`
2. **Envelope**: Server sends `aap:envelope` (always first)
3. **Streaming**: Server sends `aap:chunk` events with incrementing `seq` and `id:`
4. **Heartbeat**: Server sends `aap:heartbeat` at regular intervals (RECOMMENDED: every 15 seconds) during idle periods
5. **Completion**: Server sends `aap:complete`
6. **Close**: Server closes the connection. Client SHOULD NOT auto-reconnect after `aap:complete`

**HTTP headers:**

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

---

## 7. Multiplexing

A single SSE connection MAY carry multiple artifact streams. When multiplexing:

- Every `aap:envelope` and `aap:chunk` event MUST include an `artifact_id` field in the data payload
- The SSE `id:` field uses the format `<artifact_id>:<seq>`
- `aap:complete` and `aap:error` events MUST include `artifact_id`
- The connection closes only after all artifact streams are complete

**Example** (multiplexed chunks):

```
event: aap:chunk
id: dashboard-001:5
data: {"artifact_id":"dashboard-001","seq":5,"content":"...","flush":true}

event: aap:chunk
id: sidebar-002:2
data: {"artifact_id":"sidebar-002","seq":2,"content":"...","flush":false}

```

---

## 8. Security Considerations

- SSE connections SHOULD use TLS (HTTPS)
- Authentication SHOULD be handled via standard HTTP mechanisms (Bearer tokens, cookies)
- Servers SHOULD set appropriate CORS headers when serving cross-origin clients
- The `retry` interval SHOULD NOT be set below 1000ms to prevent reconnection storms
