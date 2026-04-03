# Agent-Artifact Protocol (AAP) Specification

**Version**: 0.1
**Status**: Draft — subject to breaking changes
**Date**: 2026-04-02

## 1. Introduction

Large language models regenerate entire artifacts on every edit — a report, a dashboard, a source file — even when only a single value changed. This wastes tokens, increases latency, and inflates cost.

The **Agent-Artifact Protocol (AAP)** is a portable, format-agnostic standard that defines how structured artifacts are declared, generated, updated, streamed, and reprovisioned with minimal token expenditure. Any LLM, agent framework, or rendering tool can implement it.

### 1.1 Design Goals

1. **Token efficiency** — express changes in the fewest tokens possible
2. **Format agnostic** — HTML, source code, JSON, YAML, Markdown, diagrams, configs
3. **Incremental by default** — full regeneration is the fallback, not the norm
4. **Streaming native** — every operation works over a stream
5. **Backward compatible** — raw content (no envelope) remains valid input
6. **Progressively adoptable** — conformance levels let implementations start simple
7. **Universal message format** — every interaction is an envelope: artifact content, diffs, projections, edit intents, results, and audit entries all share the same structure

### 1.2 Relationship to Existing Standards

| Standard | Relationship |
|---|---|
| [RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902) (JSON Patch) | Diff operations borrow semantics for JSON artifacts |
| [Unified Diff](https://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html) | Text diff operations use unified diff addressing |
| [Mustache](https://mustache.github.io/) | Template syntax is a subset of Mustache |
| [JSON Schema](https://json-schema.org/) | All protocol structures have machine-validatable schemas |

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Artifact** | A discrete unit of structured content (an HTML page, a source file, a config) |
| **Envelope** | Universal JSON message carrying artifact identity, operation metadata, and content |
| **Section** | A named, addressable region within an artifact |
| **Chunk** | A unit of streamed content within a chunk frame |
| **Operation** | The `operation` object in an envelope — metadata about the action being performed |
| **Direction** | Whether an envelope is `"input"` (to the system) or `"output"` (from the system) |
| **Generation** | The act of producing artifact content (initial creation or update) |
| **Reprovisioning** | Updating an existing artifact to a new version |
| **Token budget** | Maximum token allocation for a generation |
| **Flush point** | A semantically meaningful boundary where partial content can be rendered |
| **Orchestrator** | Agent that manages artifacts via handles and projections — never holds full content |
| **Init-agent** | Agent specialized for artifact creation — produces `name: "full"` or `name: "manifest"` envelopes |
| **Maintain-agent** | Agent specialized for edits and summaries — produces diff/section/template/projection envelopes |
| **Apply engine** | Deterministic code that resolves envelope operations against stored artifacts (CPU, not LLM) |
| **Entity state** | Lifecycle state of a managed artifact (`draft`, `published`, `archived`) |
| **Advisory lock** | Non-mandatory lock hint to coordinate concurrent editors |
| **SSE binding** | Normative Server-Sent Events wire format for streaming ([AAP-SSE](aap-sse.md)) |

---

## 3. Artifact Model

### 3.1 Envelope

Every protocol-aware payload is wrapped in an **envelope** — a JSON object with six top-level fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `protocol` | string | YES | Protocol identifier. MUST be `"aap/0.1"` |
| `id` | string | YES | Unique artifact identifier (UUID or user-supplied) |
| `version` | integer | YES | Monotonically increasing version number (starts at 1). For non-`full` operations, the apply engine validates `stored_version == version - 1` |
| `name` | string | YES | Operation discriminator (see [Section 4](#4-operations)) |
| `operation` | object | YES | Metadata about the action (see below) |
| `content` | array | YES | List of content objects — shape determined by `name` |

The `name` field determines what the envelope represents and what shape the `content` items take. There are 11 operation names:

**Artifact operations:** `full`, `diff`, `section`, `template`, `composite`, `manifest`

**Control-plane operations:** `handle`, `projection`, `intent`, `result`, `audit`

#### 3.1.1 Operation Object

The `operation` object carries metadata about the action:

| Field | Type | Required | Description |
|---|---|---|---|
| `direction` | string | YES | `"input"` (to the system) or `"output"` (from the system) |
| `format` | string | YES* | MIME type of the artifact content (`text/html`, `text/x-python`, `application/json`, etc.). *Not required for `audit` |
| `encoding` | string | no | Character encoding. Default: `"utf-8"` |
| `content_encoding` | string | no | Compression: `"gzip"` or `"zstd"`. Applied to body fields |
| `section_id` | string | no | Section this result fills (for parallel section results) |
| `token_budget` | object | no | Token budget constraints (see [Section 7](#7-token-budgeting)) |
| `tokens_used` | integer | no | Actual tokens consumed to produce this payload |
| `checksum` | string | no | `sha256:<hex>` integrity hash of the resolved content |
| `created_at` | string | no | ISO 8601 timestamp of initial creation |
| `updated_at` | string | no | ISO 8601 timestamp of this version |
| `state` | string | no | Entity lifecycle state: `"draft"`, `"published"`, `"archived"` (see [Section 10](#10-artifact-entity-state)) |
| `state_changed_at` | string | no | ISO 8601 timestamp of last state transition |

The `operation` object is extensible — implementations MAY add additional fields for vendor-specific or future extensions.

#### 3.1.2 Content Array

The `content` field is always an **array of objects**. This enables parallel operations in a single envelope — multiple diff operations, multiple edit intents, multiple audit entries — without requiring separate tool calls or API requests.

The shape of each content item is determined by `name`. See [Section 4](#4-operations) for the content schema of each operation name.

**Example** (minimal full envelope):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 1,
  "name": "full",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "body": "<!DOCTYPE html><html><body><h1>Dashboard</h1></body></html>",
      "sections": [{"id": "stats"}, {"id": "users"}]
    }
  ]
}
```

### 3.2 Sections

An artifact MAY be divided into named **sections** — addressable regions that enable targeted updates. Section definitions are carried in the `content[0].sections` array of a `name: "full"` envelope.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | YES | Unique section identifier within the artifact |
| `label` | string | no | Human-readable label |
| `start_marker` | string | no | Format-specific start boundary |
| `end_marker` | string | no | Format-specific end boundary |

Section markers are format-specific. Implementations MUST derive markers from the envelope's `operation.format` field using this table. If a section definition provides explicit `start_marker` and `end_marker`, those override the format-derived defaults.

| Format family | MIME types | Start marker | End marker |
|---|---|---|---|
| HTML / Markdown / SVG / XML | `text/html`, `text/markdown`, `image/svg+xml`, `*+xml` | `<!-- section:id -->` | `<!-- /section:id -->` |
| C-style languages | `application/javascript`, `text/typescript`, `text/x-rust`, `text/x-go`, `text/x-java`, `text/x-c`, `text/css` | `// #region id` | `// #endregion id` |
| Hash-comment languages | `text/x-python`, `text/x-ruby`, `application/x-sh`, `text/x-yaml`, `application/yaml` | `# region id` | `# endregion id` |
| JSON | `application/json` | N/A (use JSON Pointer paths via `pointer` targeting in diff operations) | N/A |
| Unknown `text/*` | Fallback | `<!-- section:id -->` | `<!-- /section:id -->` |

**Example** (HTML with sections):

```html
<!-- section:stats -->
<div class="stats">...</div>
<!-- /section:stats -->

<!-- section:users-table -->
<table>...</table>
<!-- /section:users-table -->
```

### 3.3 Version Chain

Every artifact maintains a version chain. Version numbers are monotonically increasing integers starting at 1. For any non-`full` operation, the apply engine validates that the stored version equals `version - 1` (optimistic concurrency). If the stored version does not match, the operation is rejected as a conflict.

```
v1 (full) → v2 (diff) → v3 (section) → v4 (full)
```

A `name: "full"` envelope resets the chain — no version validation is required.

---

## 4. Operations

The `name` field declares what the envelope represents and how `content` items are shaped. Producers SHOULD select the most token-efficient operation for the change at hand.

### 4.1 Full (`name: "full"`)

Complete artifact content. This is the baseline — most expensive, always correct.

**When to use**: initial creation, major rewrites, or when diff overhead exceeds content size.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `body` | string | YES | Full artifact content |
| `sections` | array | no | Section definitions (see [Section 3.2](#32-sections)) |

```json
{
  "protocol": "aap/0.1",
  "id": "report-42",
  "version": 1,
  "name": "full",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "body": "<html><body><h1>Q4 Report</h1>...</body></html>",
      "sections": [{"id": "summary"}, {"id": "charts"}]
    }
  ]
}
```

### 4.2 Diff (`name: "diff"`)

Express changes as operations against the previous version. Each `content` item is a diff operation applied sequentially.

**When to use**: small, localized changes (value updates, line insertions, deletions).

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `op` | string | YES | `"replace"`, `"insert_before"`, `"insert_after"`, `"delete"` |
| `target` | object | YES | Addressing (see below) |
| `content` | string | no | New content (required for `replace`, `insert_before`, `insert_after`) |

#### Target Addressing

A target identifies where in the artifact the operation applies. Exactly one addressing mode MUST be used:

| Address mode | Fields | Description |
|---|---|---|
| Section | `{"section": "id"}` | Target an entire section by ID |
| Line range | `{"lines": [start, end]}` | Target lines (1-indexed, inclusive) |
| Offset range | `{"offsets": [start, end]}` | Target character offsets (0-indexed, exclusive end) |
| Search | `{"search": "literal text"}` | Target first occurrence of literal text |
| Pointer | `{"pointer": "/path/to/value"}` | Target a value by JSON Pointer (RFC 6901) — for `application/json` and `application/yaml` formats |

**Pointer targeting semantics:**
- `replace`: `content` MUST be a valid JSON value. Replaces the value at the pointer location.
- `delete`: Removes the key from an object or the element from an array (shifting subsequent indices).
- `insert_before` / `insert_after`: The pointer MUST reference an array element (last segment must be a non-negative integer). Inserts the new value before/after that index.
- Non-existent paths MUST produce an error. Pointer operations do not auto-create intermediate paths.
- Re-serialization may alter original formatting and comments.

**Example** (update two stat card values in a single envelope):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 2,
  "name": "diff",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "op": "replace",
      "target": {"search": "<span class=\"stat-value\">$12,340</span>"},
      "content": "<span class=\"stat-value\">$15,720</span>"
    },
    {
      "op": "replace",
      "target": {"search": "<span class=\"stat-value\">1,205</span>"},
      "content": "<span class=\"stat-value\">1,342</span>"
    }
  ]
}
```

### 4.3 Section (`name: "section"`)

Regenerate only targeted sections. All other sections are preserved from the previous version. Each `content` item is a section replacement.

**When to use**: one or a few sections need significant changes, but the rest is unchanged.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | YES | Section ID to replace |
| `content` | string | YES | New content for this section |

**Example** (replace the users table):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 3,
  "name": "section",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "id": "users-table",
      "content": "<table><tr><th>Name</th><th>Email</th></tr>...</table>"
    }
  ]
}
```

### 4.4 Template (`name: "template"`)

Define a skeleton with named slots, then fill only the slots. Templates eliminate boilerplate regeneration.

**When to use**: generating variants of a known structure (dashboards with different data, reports with different periods, config files for different environments).

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `template` | string | YES | Template content with `{{slot_name}}` placeholders, or a registered template ID |
| `bindings` | object | YES | Map of slot name to content string |

Slot syntax follows [Mustache](https://mustache.github.io/):

- `{{name}}` — variable substitution (HTML-escaped by default)
- `{{{name}}}` — unescaped substitution
- `{{#items}}...{{/items}}` — iteration
- `{{#condition}}...{{/condition}}` — conditional block
- `{{^condition}}...{{/condition}}` — inverted conditional

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 4,
  "name": "template",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "template": "<!DOCTYPE html><html><body><h1>{{title}}</h1><div>{{{stats_html}}}</div></body></html>",
      "bindings": {
        "title": "Q1 Dashboard",
        "stats_html": "<div class='stat'><span>Revenue</span><span>$15,720</span></div>"
      }
    }
  ]
}
```

### 4.5 Composite (`name: "composite"`)

Assemble an artifact from referenced sub-artifacts or external URIs. Enables deduplication of shared components. Each `content` item is an include reference.

**When to use**: artifacts that share components (common nav bars, shared CSS, reusable code modules).

**Content item schema:**

| Field | Type | Description |
|---|---|---|
| `ref` | string | Reference to another artifact: `"artifact_id"` or `"artifact_id:section_id"` |
| `uri` | string | External URI to fetch content from |
| `content` | string | Inline content (fallback if ref/uri unavailable) |
| `hash` | string | Expected `sha256:<hex>` of resolved content |

Exactly one of `ref`, `uri`, or `content` MUST be present per item.

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "full-page",
  "version": 1,
  "name": "composite",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {"ref": "shared-header"},
    {"content": "<main><h1>Page Content</h1></main>"},
    {"ref": "shared-footer"}
  ]
}
```

### 4.6 Manifest (`name: "manifest"`)

Declare artifact structure and section assignments for parallel generation. Each `content` item contains the skeleton and section prompts.

**When to use**: parallelizing initial generation across multiple agents.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `skeleton` | string | YES | Static scaffold with section markers (boilerplate, layout, shared CSS) |
| `section_prompts` | array | YES | Per-section generation instructions |

Each `section_prompt` entry:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | YES | Section ID (matches marker in skeleton) |
| `prompt` | string | YES | Generation instruction for this section |
| `dependencies` | array | no | Section IDs that must complete before this one starts |
| `token_budget` | integer | no | Max tokens for this section |

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 1,
  "name": "manifest",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "skeleton": "<!DOCTYPE html>\n<html>\n<body>\n<!-- section:nav --><!-- /section:nav -->\n<!-- section:stats --><!-- /section:stats -->\n<!-- section:users --><!-- /section:users -->\n</body>\n</html>",
      "section_prompts": [
        {"id": "nav", "prompt": "Generate a navigation bar with logo and user menu"},
        {"id": "stats", "prompt": "Generate 4 stat cards: users, revenue, orders, uptime"},
        {"id": "users", "prompt": "Generate a users table with 50 rows", "dependencies": ["stats"]}
      ]
    }
  ]
}
```

### 4.7 Control-Plane Operations

The following operation names support the Artifact Type Interface ([Section 8](#8-artifact-type-interface)). They use the same envelope structure as artifact operations.

| Name | Direction | Purpose | Content item schema |
|---|---|---|---|
| `handle` | output | Lightweight artifact reference for orchestrators | `{sections, token_count?, state?, entity?}` |
| `projection` | output | Structured summary of an artifact | `{projection_type, token_count, sections?, changes?, outline?, summary?, statistics?}` |
| `intent` | input | Edit request from orchestrator | `{intent, target_sections?, constraints?, priority?, idempotency_key?}` |
| `result` | output | Outcome of an edit operation | `{status, mode_used, changes, tokens_used?, rejection_reason?, conflict_detail?, checksum?}` |
| `audit` | output | Operation record | `{entry_id, operation, actor, timestamp, version_before?, version_after?, detail?, status?, error?, tokens_used?}` |

See [Section 8](#8-artifact-type-interface) for detailed schemas, examples, and usage patterns.

### 4.8 Content Encoding (Compression)

Any operation MAY compress its content body fields using `operation.content_encoding`:

- `"gzip"` — gzip compression (RFC 1952)
- `"zstd"` — Zstandard compression (RFC 8878)

Compressed content MUST be base64-encoded in JSON. The `operation.checksum` field, if present, applies to the **uncompressed** content.

---

## 5. Reprovisioning

Reprovisioning is the act of updating an existing artifact. The producer selects a strategy based on the scope of change.

### 5.1 Section-First Generation (Recommended)

Producers SHOULD emit section markers on the **initial full generation**. This incurs a small overhead (~2% extra tokens for markers) but enables all subsequent updates to use `section` or `diff` operations — typically saving 90-99% of tokens per update.

**Rationale**: the upfront cost of markers is amortized across every future update. After just one `section` update, the total token spend is lower than two full regenerations.

**Guidelines for section placement**:
- Place section boundaries at **independently meaningful blocks** (navigation, stat cards, data tables, forms, sidebars)
- Aim for **5-15 sections** per artifact — too few limits granularity, too many adds overhead
- Each section should be **self-contained**: updating one section should not require changes to another
- Avoid nesting sections deeper than 2 levels

**Cost model** (N = number of future updates):
- Without sections: N full regenerations = N × full_tokens
- With sections: 1 full (with markers) + N section updates = full_tokens × 1.02 + N × section_tokens
- Break-even: 1 update (section_tokens is typically 1-10% of full_tokens)

### 5.2 Parallel Generation

When an artifact has well-defined sections, the initial generation can be **parallelized** — each section is generated by an independent agent running concurrently, then assembled into the final artifact.

#### 5.2.1 Manifest

A **manifest** declares the artifact structure and section assignments before generation begins. It is an envelope with `name: "manifest"` (see [Section 4.6](#46-manifest-name-manifest)).

#### 5.2.2 Orchestration Flow

```
                    ┌─── Agent 1 ──▶ nav section ───────┐
Manifest ──parse──▶ ├─── Agent 2 ──▶ stats section ─────┼──▶ Assembler ──▶ Full Artifact
                    ├─── Agent 3 ──▶ users section ──────┤
                    └─── Agent 4 ──▶ orders section ─────┘
                                     (waits for stats)
```

1. **Parse manifest**: extract skeleton and section prompts
2. **Dispatch**: launch one generation per section, respecting `dependencies`
3. **Collect**: each agent returns a section envelope (`name: "full"`, scoped via `operation.section_id`)
4. **Assemble**: stitch section content into the skeleton at marker positions
5. **Store**: save the assembled artifact as version 1 with all section markers intact

Sections without `dependencies` run concurrently. Sections with dependencies wait for their prerequisites to complete before starting.

#### 5.2.3 Section Results

Each parallel agent returns a **section result** — an envelope with `operation.section_id` identifying which section it fills:

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 1,
  "name": "full",
  "operation": {"direction": "output", "format": "text/html", "section_id": "stats", "tokens_used": 450},
  "content": [
    {"body": "<div class=\"stats\">...</div>"}
  ]
}
```

The assembler collects all section results and inserts each between its markers in the skeleton.

#### 5.2.4 Latency and Cost Model

| Strategy | Wall-clock latency | Total tokens | Tool calls |
|---|---|---|---|
| Sequential full | sum(section_times) | full_tokens | 1 |
| Parallel sections | max(section_times) | full_tokens + manifest_overhead | N + 1 |
| Parallel + update | max(section_times) + update_time | full_tokens + section_tokens | N + 2 |

**Manifest overhead** is minimal — the skeleton and prompts are typically 5-10% of the full artifact tokens.

#### 5.2.5 Parallel Updates

The same pattern applies to updates. When multiple sections need regeneration, dispatch them in parallel using a manifest with only the sections that changed:

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 2,
  "name": "manifest",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "skeleton": null,
      "section_prompts": [
        {"id": "stats", "prompt": "Update stat cards with Q2 data"},
        {"id": "orders", "prompt": "Add 10 new order rows"}
      ]
    }
  ]
}
```

Only the listed sections are regenerated. The assembler merges results into the existing artifact, preserving unchanged sections.

### 5.3 Strategy Selection Guide

| Change scope | Recommended operation | Token savings |
|---|---|---|
| Single value change | `diff` (search/replace) | ~95-99% |
| Few lines changed | `diff` (line range) | ~90-98% |
| One section rewritten | `section` | ~80-95% |
| Multiple sections rewritten | `section` | ~50-80% |
| Same structure, different data | `template` | ~90-98% |
| Complete rewrite | `full` | 0% (baseline) |

### 5.4 Version Chain Integrity

1. Each non-`full` envelope MUST have `version` equal to `stored_version + 1`
2. The apply engine MUST verify this before applying
3. On mismatch: reject the operation, notify the producer of the current version
4. The producer SHOULD re-derive its update against the correct version

### 5.5 Rollback

Consumers SHOULD maintain a configurable version history (default: 10 versions). Rollback replaces the current content with a previous version and increments the version number.

---

## 6. Streaming Protocol

Streaming is orthogonal to operation name — any operation can be streamed. Streamed payloads are delivered as **JSONL** (one JSON object per line).

### 6.1 Chunk Frame

Each streamed unit is a **chunk frame**:

| Field | Type | Required | Description |
|---|---|---|---|
| `seq` | integer | YES | Monotonically increasing sequence number (starts at 0) |
| `content` | string | YES | Chunk payload |
| `section_id` | string | no | Section being streamed (if applicable) |
| `flush` | boolean | no | Hint to render/apply accumulated content. Default: `false` |
| `final` | boolean | no | `true` on the last chunk. Default: `false` |

The first chunk frame (`seq: 0`) SHOULD include the envelope metadata (all fields except `content`) in an `envelope` field. Subsequent frames carry only chunk data.

**Example** (streaming a full artifact):

```jsonl
{"seq":0,"envelope":{"protocol":"aap/0.1","id":"doc-1","version":1,"name":"full","operation":{"direction":"output","format":"text/html"}},"content":"<!DOCTYPE html><html>","flush":true,"final":false}
{"seq":1,"content":"<head><title>Report</title></head>","flush":true,"final":false}
{"seq":2,"content":"<body><h1>Q4 Report</h1>","flush":false,"final":false}
{"seq":3,"content":"<p>Revenue increased by 15%.</p></body></html>","flush":true,"final":true}
```

### 6.2 Flush Strategies

Producers SHOULD emit `flush: true` at semantically meaningful boundaries:

| Strategy | Description | Flush overhead | Render quality |
|---|---|---|---|
| **Token-aligned** | Flush every token | High | Smooth but expensive |
| **Syntax-aligned** | Flush at tag/statement boundaries | Low | Clean partial renders |
| **Size-aligned** | Flush every N bytes | Low | May split mid-tag |
| **Adaptive** | Start small (responsiveness), grow chunks over time | Low | Best overall |

**Recommended**: adaptive strategy with syntax-aligned flush points.

### 6.3 Transport

The protocol is transport-agnostic. Reference transports:

| Transport | Description |
|---|---|
| **File write + poll** | Write JSONL to a file; consumer polls for changes |
| **Server-Sent Events** | Each chunk frame is an SSE `data:` line |
| **WebSocket** | Each chunk frame is a WebSocket text message |
| **stdio** | Each chunk frame is a line on stdout |

A normative SSE transport binding is defined in [AAP-SSE](aap-sse.md).

---

## 7. Token Budgeting

### 7.1 Budget Declaration

The `operation.token_budget` object declares constraints:

| Field | Type | Description |
|---|---|---|
| `max_tokens` | integer | Maximum content tokens (excludes envelope overhead) |
| `priority` | string | `"completeness"` (prefer full content), `"brevity"` (prefer concise), `"fidelity"` (prefer accuracy) |
| `max_sections` | integer | Maximum sections to regenerate (for `section` operations) |

### 7.2 Budget Accounting

- **Content tokens**: tokens in the artifact payload (what the user sees)
- **Overhead tokens**: envelope metadata, framing, operation descriptions
- The budget applies to **content tokens only**
- Producers MUST NOT exceed `max_tokens`
- Producers SHOULD select the most token-efficient operation to stay within budget

### 7.3 Reporting

The final envelope (or final chunk frame) MUST include `operation.tokens_used` — the actual content tokens consumed. This enables consumers to track token efficiency over time.

---

## 8. Artifact Type Interface

When agents manage artifacts through conversation, three costs compound: **context bloat** (KV cache grows with edit history), **token waste** (content written twice — once to read, once to regenerate), and **hallucination** (agents "remember" content they no longer have in context). The Artifact Type Interface eliminates all three by defining a contract built on two principles:

1. **The artifact is the only persistent state.** Between edits, everything is discarded — system prompts, intents, envelope operations. Only the artifact revision survives.
2. **The AI dispatches; the CPU splices.** Agents produce envelope operations (diffs, section updates). The apply engine resolves them against the stored artifact deterministically, at zero token cost. Content is never written twice.

This contract is realized through a **two-agent topology** with distinct specializations:

- **Init-agent** — specialized for creation. Takes generation instructions, produces `name: "full"` or `name: "manifest"` envelopes with well-placed section markers. Runs once per artifact (or on re-initialization). After completion, context is discarded.
- **Maintain-agent** — specialized for reading existing content and producing AAP envelopes. Has two output modes:
  - **Edit:** receives artifact + edit intent → produces `name: "diff"`, `name: "section"`, or `name: "template"` envelopes
  - **Summarize:** receives artifact + summarize request → produces `name: "projection"` envelopes
  - Context per call: `[system prompt] + [artifact vN] + [instruction]`. Discarded after each call.
- **Apply engine** — deterministic code (not an LLM). Receives envelopes, resolves them against stored artifacts (~2μs, 0 tokens), validates operations, stores new revisions.

The init-agent and maintain-agent are separate because they have fundamentally different jobs. The init-agent is *generative* — it creates structure, places section boundaries, produces layout. The maintain-agent is *surgical* — it reads existing content and produces minimal diffs. Different system prompts, potentially different models, different temperature settings. Combining them into a single agent bloats both the system prompt and the context, increasing hallucination surface and cost without benefit.

```
Orchestrator (handles, projections, user conversation)
    │
    ├── create ──→ Init-agent ──→ name:"full" envelope ──→ Apply engine ──→ Store ──→ name:"handle"
    │
    ├── summarize ──→ Maintain-agent ──→ name:"projection" envelope ──→ (returned to orchestrator)
    │
    └── edit ──→ Maintain-agent ──→ name:"diff" envelope ──→ Apply engine ──→ Store ──→ name:"result"
```

### 8.1 Memory Model

Each agent call is a **stateless dispatch** — an independent inference call with no conversation history. The artifact is the single source of truth.

**Init-agent context (runs once):**

```
[System prompt (creation-specialized)] + [Generation instructions]
                    ↓ produces ↓
[name:"full" envelope with section markers]
                    ↓ apply engine (CPU) ↓
[Artifact v1] ← stored, context discarded
```

**Maintain-agent context (runs per edit):**

```
[System prompt (maintenance-specialized)] + [Artifact vN] + [Edit intent]
                    ↓ produces ↓
[name:"diff" envelope with operations]
                    ↓ apply engine (CPU) ↓
[Artifact vN+1] ← sole survivor, context discarded
```

**Maintain-agent context (runs per summarize):**

```
[System prompt (maintenance-specialized)] + [Artifact vN] + ["Summarize: structure"]
                    ↓ produces ↓
[name:"projection" envelope] ← returned to orchestrator, agent context discarded
```

In every case: system prompt is re-injected next time. Intent is discarded. Envelope operations are consumed by the apply engine and discarded. Previous edits never existed in the current context. Only the artifact persists.

**Normative requirements:**

- Implementations MUST NOT accumulate edit history in any agent's context
- Each agent call MUST start with a fresh context
- The maintain-agent MUST produce envelope operations (`diff`, `section`, or `template`) on edits — the apply engine resolves them against the stored artifact
- The maintain-agent SHOULD NOT produce `name: "full"` envelopes on edits — this defeats the model by writing content tokens twice
- The init-agent SHOULD produce artifacts with section markers ([Section 5.1](#51-section-first-generation-recommended)) to enable efficient subsequent edits
- The artifact content is the single source of truth, not conversation memory

#### 8.1.1 Cost Model

**Per-edit cost (maintain-agent):**

| Component | Input tokens | Output tokens | Persists? |
|---|---|---|---|
| System prompt | ~fixed | — | No (re-injected each call) |
| Artifact revision | ~artifact_size | — | **Yes** (as vN+1 after apply) |
| Edit intent | ~small | — | No |
| Envelope operations | — | ~50-500 (diff) | No (consumed by apply engine) |
| **Total per edit** | **system + artifact + intent** | **~50-500** | **artifact only** |

Compare the naive approach: `~artifact_size` input + `~artifact_size` output + growing conversation history per edit. Output tokens are 3-5× more expensive than input tokens, so the reduction from `~artifact_size` output to `~50-500` output is where the savings concentrate.

> **Non-normative note:** The ~50-500 output token estimate is derived from hand-crafted envelope benchmarks (Appendix B). AI-generated envelopes from natural language intents may produce larger diffs or fall back to section-mode rewrites when a targeted diff would suffice. Implementations SHOULD track actual output token counts via the audit log to calibrate expectations.

#### 8.1.2 Amortization

The initial creation (init-agent, `name: "full"`) is the most expensive operation — full output tokens to produce the artifact with section markers. This is a one-time investment that makes every subsequent edit cheap:

| | Initial create | Edit 1 | Edit 2 | ... | Edit N | Total output |
|---|---|---|---|---|---|---|
| **Dispatch model** | S | ~50 | ~50 | | ~50 | S + 50N |
| **Naive (full regen)** | S | S | S | | S | S × (N+1) |

Where S = artifact size in output tokens. Break-even: **one edit**. After a single diff update, total spend is lower than two full regenerations. By edit N, savings ≈ `(N-1) × S` output tokens.

#### 8.1.3 Anti-Hallucination Properties

The architecture structurally reduces hallucination through role separation:

- The **orchestrator** never sees full artifact content. It holds only handles and projections. It can describe *intent* but cannot hallucinate *content* it has never seen.
- The **init-agent** produces content from instructions — hallucination risk is inherent to generation, but its context is clean.
- The **maintain-agent** sees the *actual current revision*, injected fresh from storage. It produces diffs against real content, not imagined content.
- The **apply engine** is deterministic code. It either applies the operations correctly or returns an error.

> **Non-normative note:** The maintain-agent *can* still hallucinate envelope operations — for example, targeting a search string that doesn't exist. However, the risk is structurally lower because: (1) the context contains *only* the artifact and the instruction; (2) the apply engine validates operations deterministically; (3) the artifact is always smaller than a full conversation thread. Implementations SHOULD track hallucination rates via the audit log. See [Section 8.5.4](#854-error-recovery) for the recommended recovery flow.

### 8.2 Handle (`name: "handle"`)

A **handle** is an envelope the orchestrator holds instead of full artifact content. It provides enough metadata for decision-making without consuming context budget.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `sections` | array of strings | YES | Section IDs present in the artifact |
| `token_count` | integer | no | Approximate token count of the full artifact |
| `state` | string | no | Entity lifecycle state |
| `entity` | object | no | Entity metadata (see [Section 10.2](#102-entity-metadata)) |

> **Non-normative note:** Orchestrators SHOULD independently track the version of their most recent projection to detect staleness (compare against `handle.version`).

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 5,
  "name": "handle",
  "operation": {"direction": "output", "format": "text/html", "state": "published", "updated_at": "2026-03-29T14:30:00Z"},
  "content": [
    {"sections": ["nav", "stats", "users", "orders"], "token_count": 10240}
  ]
}
```

### 8.3 Projection (`name: "projection"`)

A **projection** is an envelope containing a compact, structured summary of an artifact. It gives the orchestrator enough information to make decisions without loading full content.

#### 8.3.1 Projection Types

| Type | Description | Approximate cost vs full artifact |
|---|---|---|
| `structure` | Section IDs, labels, token counts. No content | 5-10% |
| `content_summary` | Natural-language summary of what the artifact contains | 10-20% |
| `change_summary` | What changed between two versions | 2-5% |
| `statistics` | Numerical metrics: token count, section count, word count, timestamps | ~50-100 tokens (fixed) |
| `full_summary` | Combined `structure` + `content_summary` | 15-25% |

> **Non-normative note:** `structure` and `statistics` projections can be computed deterministically by parsing section markers and counting tokens — no inference call required. `content_summary`, `change_summary`, and `full_summary` require an inference call via the maintain-agent. Implementations SHOULD prefer CPU-computable projections when the orchestrator only needs structural information.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `projection_type` | string | YES | One of the types above |
| `token_count` | integer | YES | Token count of the full artifact (not the projection) |
| `sections` | array | no | Section summaries (for `structure` and `full_summary`) |
| `changes` | array | no | Change descriptions (for `change_summary`) |
| `outline` | string | no | Textual outline or table of contents (for `structure`) |
| `summary` | string | no | Natural-language content summary (for `content_summary`) |
| `statistics` | object | no | Numerical metrics (for `statistics`) |

Each section summary contains: `id`, `label`, `token_count`, `summary`.

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 5,
  "name": "projection",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {
      "projection_type": "structure",
      "token_count": 10240,
      "outline": "HTML dashboard with 4 main sections",
      "sections": [
        {"id": "nav", "label": "Navigation", "token_count": 820, "summary": "Top nav bar with logo, search, and user menu"},
        {"id": "stats", "label": "Statistics Cards", "token_count": 1200, "summary": "4 stat cards: users (1,247), revenue ($15,720), orders (384), uptime (99.7%)"}
      ]
    }
  ]
}
```

#### 8.3.2 Staleness

A projection is stale when its `version` is less than the artifact's current version. Orchestrators MUST compare the projection's `version` against the handle's `version`.

When a projection is stale, the orchestrator SHOULD request a `change_summary` projection to understand what changed — rather than requesting a full new projection. This keeps the catch-up cost proportional to the changes, not the artifact size.

### 8.4 Edit Intent and Edit Result

The edit delegation pattern separates **intent** from **execution**. The orchestrator formulates *what* should change; the maintain-agent — with the actual content in context — decides *how* and produces the minimal envelope operations.

#### 8.4.1 Intent (`name: "intent"`)

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | string | YES | Natural-language description of the desired change |
| `target_sections` | array of strings | no | Section IDs the edit should affect (scoping hint) |
| `constraints` | object | no | Constraints: `max_tokens`, `preserve_structure`, `mode_hint`, `validation` |
| `priority` | string | no | `"completeness"`, `"brevity"`, `"fidelity"` |
| `idempotency_key` | string | no | Client-supplied key to prevent duplicate execution |

The `intent` field SHOULD be self-contained: any data the maintain-agent needs that is not present in the artifact itself SHOULD be included in the intent text.

Multiple intents can be batched in a single envelope for parallel processing:

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 5,
  "name": "intent",
  "operation": {"direction": "input", "format": "text/html"},
  "content": [
    {"intent": "Update revenue to $18,500", "target_sections": ["stats"]},
    {"intent": "Add 10 new order rows", "target_sections": ["orders"]}
  ]
}
```

#### 8.4.2 Result (`name: "result"`)

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | string | YES | `"applied"`, `"rejected"`, `"partial"`, `"conflict"` |
| `mode_used` | string | YES | Operation name the maintain-agent selected |
| `changes` | array | YES | Summary of what changed (per-change: `section_id`, `description`) |
| `tokens_used` | integer | no | Output tokens consumed (the envelope operations, not the artifact) |
| `rejection_reason` | string | no | Why the edit was rejected |
| `conflict_detail` | string | no | Version mismatch information |
| `checksum` | string | no | `sha256:<hex>` of the artifact after the edit |

**Status semantics:**

| Status | Meaning |
|---|---|
| `applied` | Edit fully executed as intended |
| `rejected` | Edit could not be performed (invalid intent, constraint violation, validation failure) |
| `partial` | Some changes succeeded, others did not. `changes` lists what was applied |
| `conflict` | Version mismatch — the artifact was modified since the intent was formulated |

On `conflict`, the orchestrator SHOULD: request a `change_summary` projection to understand what changed, then reformulate its intent against the current version.

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 6,
  "name": "result",
  "operation": {"direction": "output", "format": "text/html", "tokens_used": 65, "checksum": "sha256:a1b2c3..."},
  "content": [
    {
      "status": "applied",
      "mode_used": "diff",
      "changes": [{"section_id": "stats", "description": "Updated revenue to $18,500"}]
    }
  ]
}
```

#### 8.4.3 Conflict Resolution Flow

```
Orchestrator                        Store / Maintain-agent
    |                                       |
    |── name:"intent" (version=5) ─────────▶|
    |                                       |── stored is v7 ──▶ conflict
    |◀── name:"result" (status: conflict) ──|
    |                                       |
    |── name:"projection" request ─────────▶|
    |◀── name:"projection" (changes v5→v7) ─|
    |                                       |
    |── name:"intent" (version=7) ─────────▶|
    |                                       |── inject artifact v7 + intent
    |                                       |── maintain-agent produces diff
    |                                       |── apply engine → v8
    |◀── name:"result" (status: applied) ───|
```

#### 8.4.4 Error Recovery

When the maintain-agent hallucinates a bad diff — for example, targeting a search string that doesn't exist — the apply engine rejects the operation. The result envelope returns `status: "rejected"` with a `rejection_reason`.

**Recommended recovery flow:**

1. Orchestrator reads the `rejection_reason`
2. Orchestrator requests a `content_summary` projection of the relevant section
3. Orchestrator reformulates the intent with more specific context from the projection
4. Retry with the maintain-agent
5. If repeated failures, escalate to re-initialization: archive the current artifact and call the init-agent

> **Restructuring:** When an artifact's section topology is fundamentally inadequate, the recommended approach is to archive the existing artifact and create a new one via the init-agent. The init-agent's instructions MAY include a projection of the old artifact for continuity. There is no in-place restructuring operation — restructuring is creation.

### 8.5 Audit (`name: "audit"`)

Every operation on an artifact produces an audit entry. The audit log enables the orchestrator to maintain awareness of what has been asked and what was produced — without holding full content.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `entry_id` | string | YES | Unique audit entry identifier |
| `operation` | string | YES | `"create"`, `"read"`, `"summarize"`, `"edit"`, `"state_transition"` |
| `actor` | string | YES | Principal that performed the operation (`type:id` format) |
| `timestamp` | string | YES | ISO 8601 timestamp |
| `version_before` | integer | no | Artifact version before the operation |
| `version_after` | integer | no | Artifact version after the operation |
| `detail` | object | no | Operation-specific detail |
| `status` | string | no | `"success"`, `"failure"`, `"partial"`. Default: `"success"` |
| `error` | string | no | Error description if `status` is `"failure"` |
| `tokens_used` | integer | no | Tokens consumed by the operation |

Failed edits MUST produce audit entries. The `status` field is `"failure"`, the `error` field describes why, and `detail.intent` preserves the original intent.

Multiple audit entries can be batched in a single envelope:

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 6,
  "name": "audit",
  "operation": {"direction": "output"},
  "content": [
    {
      "entry_id": "audit-001",
      "operation": "edit",
      "actor": "agent:orchestrator",
      "timestamp": "2026-03-29T14:02:00Z",
      "version_before": 5,
      "version_after": 6,
      "status": "success",
      "tokens_used": 65,
      "detail": {"intent": "Update revenue to $18,500", "mode_used": "diff"}
    }
  ]
}
```

> **Non-normative note:** Query parameters for the audit log (filtering by time, operation type, actor, status) are implementation-specific. The protocol defines the audit entry schema, not the query API.

### 8.6 Operations Summary

The Artifact Type Interface defines five abstract operations, all expressed as envelopes:

| Operation | Input envelope | Output envelope | Description |
|---|---|---|---|
| `create` | `name: "full"` or `name: "manifest"` | `name: "handle"` | Create artifact, return handle |
| `read` | *(implementation-specific)* | `name: "full"` (scoped) | Read content — for agent injection, NOT orchestrators |
| `summarize` | *(implementation-specific)* | `name: "projection"` | Compact summary for orchestrator |
| `edit` | `name: "intent"` | `name: "result"` | Dispatch edit via stateless model |
| `audit` | *(implementation-specific)* | `name: "audit"` | Retrieve interaction history |

**Normative:** Orchestrators MUST use projections rather than reads to inspect artifact content, and MUST use intents rather than directly producing content envelopes.

> **Parallel edits:** When multiple independent edits target non-overlapping sections, the orchestrator MAY batch multiple intents in a single `name: "intent"` envelope. The resulting envelopes are applied sequentially by the apply engine. This follows the same pattern as parallel manifest updates ([Section 5.2.5](#525-parallel-updates)).

---

## 9. Scope: Text Artifacts

AAP produces structured text artifacts — HTML, SVG, source code, configuration files, Markdown, and similar text-based formats. How those artifacts are displayed or rendered is **outside the protocol's scope** and is the responsibility of the consuming application.

Consumers may render artifacts using browsers, PDF generators, terminal viewers, IDE panels, or any other tool appropriate to the artifact's MIME type. The `operation.format` field communicates the artifact's content type to aid consumers in selecting an appropriate renderer, but the protocol does not prescribe rendering behavior.

> **Non-normative note:** For binary output formats (PDF, PPTX, DOCX, images), the recommended pattern is to produce the intermediate text representation (HTML, SVG, XML) as the AAP artifact, then use an external tool to convert to the final format. This keeps the protocol's diff, section, and template operations fully functional on the artifact content.

---

## 10. Artifact Entity State

Artifacts can optionally be treated as **managed entities** with lifecycle states, ownership, relationships, and expiration. All entity fields are optional — Level 0-3 consumers ignore them.

### 10.1 State Machine

```
              publish           archive
  ┌─────────┐ ──────▶ ┌───────────┐ ──────▶ ┌──────────┐
  │  draft   │         │ published  │         │ archived  │
  └─────────┘ ◀────── └───────────┘         └──────────┘
              unpublish          restore
                                  ◀──────────────────────
```

| State | Description |
|---|---|
| `draft` | Work-in-progress. MAY be updated freely. Not visible to downstream consumers |
| `published` | Stable release. Updates create new versions; artifact is considered live |
| `archived` | Retired. Read-only. No further updates permitted until restored |

**Transitions:**

| Transition | From | To |
|---|---|---|
| `publish` | draft | published |
| `unpublish` | published | draft |
| `archive` | published | archived |
| `restore` | archived | published |

State is carried in the `operation.state` field. State transitions are recorded in `operation.state_changed_at`.

### 10.2 Entity Metadata

The optional `entity` object (carried in `content` for `name: "handle"` envelopes) holds ownership and organizational metadata:

| Field | Type | Required | Description |
|---|---|---|---|
| `owner` | string | no | Owning user or system identifier |
| `created_by` | string | no | Creator identifier |
| `tags` | array of strings | no | Freeform classification tags |
| `permissions` | object | no | Access control (see [Section 10.3](#103-permissions)) |
| `collection` | string | no | Workspace or collection grouping identifier |
| `ttl` | integer | no | Time-to-live in seconds from `operation.updated_at` |
| `expires_at` | string | no | ISO 8601 expiration timestamp (takes precedence over `ttl`) |
| `relationships` | array | no | Links to other artifacts (see [Section 10.4](#104-relationships)) |

**Example** (handle envelope with entity metadata):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 3,
  "name": "handle",
  "operation": {"direction": "output", "format": "text/html", "state": "published"},
  "content": [
    {
      "sections": ["nav", "stats", "users"],
      "token_count": 10240,
      "entity": {
        "owner": "user:alice",
        "created_by": "agent:claude",
        "tags": ["dashboard", "q4", "revenue"],
        "collection": "workspace:finance-team",
        "ttl": 86400,
        "permissions": {
          "read": ["team:finance", "user:bob"],
          "write": ["user:alice", "agent:claude"],
          "admin": ["user:alice"]
        }
      }
    }
  ]
}
```

### 10.3 Permissions

The `permissions` object uses a role-based model:

| Field | Type | Description |
|---|---|---|
| `read` | array of strings | Principals that can read the artifact |
| `write` | array of strings | Principals that can update the artifact |
| `admin` | array of strings | Principals that can change state, permissions, and delete |

Principal identifiers follow the format `<type>:<id>` (e.g., `"user:alice"`, `"team:finance"`, `"agent:claude"`, `"*"` for public). Enforcement is outside protocol scope — this is metadata for the platform to act on.

### 10.4 Relationships

Artifacts can declare typed relationships:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | YES | Relationship type: `"depends_on"`, `"parent"`, `"child"`, `"derived_from"`, `"supersedes"`, `"related"` |
| `target` | string | YES | Target artifact ID |
| `version` | integer | no | Specific version of the target (omit for latest) |

Relationships are informational. Consumers MAY use them for dependency resolution but MUST NOT require them for correct envelope processing.

### 10.5 Optimistic Locking

The `version` field provides optimistic concurrency control. For non-`full` operations, the apply engine validates `stored_version == version - 1`. State transitions follow the same rule.

For advisory (non-mandatory) locking, an optional `lock` object may be included in `content`:

| Field | Type | Description |
|---|---|---|
| `held_by` | string | Principal holding the lock |
| `acquired_at` | string | ISO 8601 timestamp |
| `ttl` | integer | Lock duration in seconds (auto-releases after expiry) |

Advisory locks are hints only. The version mechanism remains the authoritative concurrency control.

### 10.6 TTL and Expiration

- When `ttl` is set, the artifact expires at `operation.updated_at + ttl` seconds
- When `expires_at` is set, it takes precedence over `ttl`
- Expired artifacts SHOULD transition to `"archived"` state automatically
- Consumers SHOULD check expiration on read and treat expired artifacts as archived

---

## 11. Conformance Levels

Implementations declare their conformance level. Each level is a superset of the previous.

### Level 0 — Basic

- MUST parse and produce valid envelopes
- MUST support `name: "full"`
- MUST validate `protocol` field

### Level 1 — Incremental

- Level 0, plus:
- MUST support `name: "diff"` with all addressing modes (section, line, offset, search)
- MUST support `name: "section"`
- MUST maintain version chain and enforce version concurrency

### Level 2 — Template

- Level 1, plus:
- MUST support `name: "template"` with Mustache-subset slot syntax
- MUST support template registration (store and reuse by ID)

### Level 3 — Full Protocol

- Level 2, plus:
- MUST support `name: "composite"` with ref, uri, and content includes
- MUST support `operation.content_encoding` (gzip and zstd)
- MUST support streaming chunk frames (JSONL)
- MUST support token budgeting (`operation.token_budget` and `operation.tokens_used`)
- MUST support adaptive flush strategy

### Level 4 — Extended

- Level 3, plus:
- MUST support SSE transport binding ([AAP-SSE](aap-sse.md))
- MUST support `operation.state` and enforce state machine transitions ([Section 10.1](#101-state-machine))
- MUST support entity metadata storage and retrieval ([Section 10.2](#102-entity-metadata))
- MUST enforce TTL/expiration ([Section 10.6](#106-ttl-and-expiration))

### Application Profile: Managed Artifacts

Levels 0-4 above are **wire-format conformance** — they define which data shapes an implementation can parse and produce. The Managed Artifacts profile is **architectural conformance** — it defines how agents interact with artifacts at runtime via the two-agent topology described in [Section 8](#8-artifact-type-interface). It requires Level 4 as a prerequisite.

- Level 4, plus:
- MUST implement the Artifact Type Interface ([Section 8](#8-artifact-type-interface)): create, read, summarize, edit, audit
- MUST support the two-agent topology: init-agent for creation, maintain-agent for edits and summarization
- MUST support the stateless dispatch memory model — no edit history accumulates in any agent's context
- The maintain-agent MUST produce `diff`, `section`, or `template` envelopes, not `full`, on edits
- MUST support all five control-plane envelope types: `handle`, `projection`, `intent`, `result`, `audit`
- MUST support all four result status codes: `applied`, `rejected`, `partial`, `conflict`
- MUST produce audit entries for every operation, including failures
- Orchestrators MUST use projections rather than reads for context inspection

---

## 12. Security Considerations

- **Content injection**: consumers MUST sanitize artifact content before displaying in privileged contexts (e.g., web browsers). Content display and sandboxing are consumer responsibilities outside the protocol scope
- **URI resolution**: `composite` URIs MUST be validated against an allowlist; arbitrary URI fetch is a server-side request forgery (SSRF) risk
- **Checksum verification**: consumers SHOULD verify `operation.checksum` when present to detect tampering or corruption
- **Token budget enforcement**: producers MUST NOT exceed declared budgets; consumers SHOULD reject payloads that claim to use fewer tokens than they actually contain
- **Entity permissions**: `permissions` in the entity object are metadata only — consumers MUST enforce access control at the platform level, not rely solely on envelope metadata

---

## 13. IANA Considerations

This specification does not require any IANA registrations. The `operation.format` field uses existing MIME types.

---

## Appendix A: JSON Schemas

Machine-validatable schemas for all protocol structures are provided in the `schemas/` directory:

- [`artifact-envelope.json`](schemas/artifact-envelope.json) — Envelope schema (covers all 11 operation names)
- [`diff-operation.json`](schemas/diff-operation.json) — Diff operation schema (content items for `name: "diff"`)
- [`template-binding.json`](schemas/template-binding.json) — Template binding schema
- [`chunk-frame.json`](schemas/chunk-frame.json) — Streaming chunk frame schema
- [`entity-metadata.json`](schemas/entity-metadata.json) — Entity metadata schema
- [`relationship.json`](schemas/relationship.json) — Artifact relationship schema
- [`sse-error.json`](schemas/sse-error.json) — SSE error event schema

## Appendix B: Token Savings Reference

Empirical measurements from the reference implementation using a 40KB HTML dashboard artifact:

| Edit scenario | Full tokens | Diff tokens | Savings | Section tokens | Savings | Template tokens | Savings |
|---|---|---|---|---|---|---|---|
| Change 1 stat value | ~10,000 | ~50 | 99.5% | N/A | — | N/A | — |
| Add 5 table rows | ~10,000 | ~300 | 97.0% | ~1,000 | 90.0% | N/A | — |
| Update all CSS colors | ~10,000 | ~700 | 93.0% | ~1,500 | 85.0% | N/A | — |
| New data, same layout | ~10,000 | N/A | — | N/A | — | ~400 | 96.0% |

*Values are approximate; see `ag-aap-bench` for current measurements.*
