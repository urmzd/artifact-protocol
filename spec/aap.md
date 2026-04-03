# Agent-Artifact Protocol (AAP) Specification

**Version**: 0.1
**Status**: Draft — subject to breaking changes
**Date**: 2026-04-02

## 1. Introduction

Large language models regenerate entire artifacts on every edit — a report, a dashboard, a source file — even when only a single value changed. This wastes tokens, increases latency, and inflates cost.

The **Agent-Artifact Protocol (AAP)** is a portable, format-agnostic standard that defines how structured artifacts are declared, generated, updated, and reprovisioned with minimal token expenditure. Any LLM, agent framework, or rendering tool can implement it.

### 1.1 Design Goals

1. **Token efficiency** — express changes in the fewest tokens possible
2. **Format agnostic** — HTML, source code, JSON, YAML, Markdown, diagrams, configs
3. **Incremental by default** — full regeneration is the fallback, not the norm
4. **Backward compatible** — raw content (no envelope) remains valid input
5. **Progressively adoptable** — conformance levels let implementations start simple

### 1.2 Relationship to Existing Standards

| Standard | Relationship |
|---|---|
| [RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902) (JSON Patch) | Edit operations borrow semantics for JSON artifacts |
| [JSON Schema](https://json-schema.org/) | All protocol structures have machine-validatable schemas |

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Artifact** | A discrete unit of structured content (an HTML page, a source file, a config) |
| **Envelope** | JSON message carrying artifact identity, metadata, and content |
| **Target** | A named, addressable region within an artifact, marked by `<aap:target id="...">` |
| **Generation** | The act of producing artifact content (initial creation or update) |
| **Reprovisioning** | Updating an existing artifact to a new version |
| **Token budget** | Maximum token allocation for a generation |
| **Handle** | Lightweight reference returned after any mutation — contains artifact ID, version, token count, and optional content |
| **Orchestrator** | Agent that manages artifacts via handles — never holds full content |
| **Init context** | Secondary context specialized for artifact creation — produces `name: "synthesize"` envelopes. May be an LLM call, agent, tool invocation, or any bounded execution context |
| **Maintain context** | Secondary context specialized for edits — produces `name: "edit"` envelopes. Context per call: artifact + message. Discarded after each call |
| **Apply engine** | Deterministic code that resolves envelope operations against stored artifacts: `f(artifact, operation) -> (artifact, handle)`. Artifact is stored; handle is returned. CPU, not LLM |
| **Entity state** | Lifecycle state of a managed artifact (`draft`, `published`, `archived`) |
| **Advisory lock** | Non-mandatory lock hint to coordinate concurrent editors |

---

## 3. Artifact Model

### 3.1 Envelope

Every protocol-aware payload is wrapped in an **envelope** — a JSON object with six top-level fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `protocol` | string | YES | Protocol identifier. MUST be `"aap/0.1"` |
| `id` | string | YES | Unique artifact identifier (UUID or user-supplied) |
| `version` | integer | YES | Monotonically increasing version number (starts at 1). For `edit` operations, the apply engine validates `stored_version == version - 1` |
| `name` | string | YES | Operation discriminator (see [Section 4](#4-operations)) |
| `meta` | object | YES | Metadata about the action (see below) |
| `content` | array | YES | List of content objects — shape determined by `name` |

The `name` field determines what the envelope represents and what shape the `content` items take. There are 3 envelope types:

| Name | Description |
|---|---|
| `synthesize` | Full artifact generation (input) |
| `edit` | Targeted changes via Target union (input) |
| `handle` | Lightweight artifact reference returned after any mutation (output) |

#### 3.1.1 Meta Object

The `meta` object carries metadata about the action:

| Field | Type | Required | Description |
|---|---|---|---|
| `format` | string | YES | MIME type of the artifact content (`text/html`, `text/x-python`, `application/json`, etc.) |
| `tokens_used` | integer | no | Actual tokens consumed to produce this payload |
| `checksum` | string | no | `sha256:<hex>` integrity hash of the resolved content |
| `state` | string | no | Entity lifecycle state: `"draft"`, `"published"`, `"archived"` (see [Section 8](#8-artifact-entity-state)) |

The `meta` object is extensible — implementations MAY add additional fields for vendor-specific or future extensions.

#### 3.1.2 Content Array

The `content` field is always an **array of objects**. This enables parallel operations in a single envelope — multiple edit operations in a single envelope — without requiring separate tool calls or API requests.

The shape of each content item is determined by `name`. See [Section 4](#4-operations) for the content schema of each operation name.

**Example** (minimal synthesize envelope):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 1,
  "name": "synthesize",
  "meta": {"format": "text/html"},
  "content": [
    {
      "body": "<!DOCTYPE html><html><body><h1>Dashboard</h1></body></html>"
    }
  ]
}
```

### 3.2 Targets

An artifact MAY contain named **targets** — addressable regions identified by stable IDs. Targets use a single universal marker format:

| Format | Start marker | End marker |
|---|---|---|
| All text formats | `<aap:target id="ID">` | `</aap:target>` |
| JSON (`application/json`) | N/A (use JSON Pointer paths via `pointer` targeting in edit operations) | N/A |

Each target ID MUST be unique within the artifact. Targets MAY nest — a coarse-grained target can contain fine-grained targets within it.

> **Design note:** LLMs reliably reference identifiers — the same mechanism behind citations, anchor links, and XML attributes. ID-based targeting eliminates the most common diff failure mode: hallucinated search strings. The init context places targets on updatable regions, the maintain context references them by ID. No literal text reproduction required.

**Guidelines for target placement:**
- Place targets at **every granularity that changes independently** — structural blocks (navigation, stat cards, data tables) and leaf values (individual numbers, status badges, config values)
- Use **descriptive, stable IDs** that describe the role, not the current value (e.g., `revenue-value`, `user-count`, `nav`, `users-table`)
- Aim for **5-15 coarse targets** per artifact with **fine-grained targets** on individually-updatable values within them
- Target placement is **preference-driven and prompt-optimizable** — the init context's system prompt can instruct where targets are most likely to be revised based on the artifact's purpose. A dashboard's stat values, a form's validation messages, a config's environment-specific fields — these are high-churn locations that benefit most from fine-grained targets
- Targets MAY carry an optional `type` attribute as a classification hint (e.g., `type="section"`, `type="value"`). The apply engine ignores `type` — it is metadata for producers and consumers

**Example:**

```html
<aap:target id="stats">
<div class="stat-card">
  <h3>Revenue</h3>
  <span class="value"><aap:target id="revenue-value">$12,340</aap:target></span>
  <small><aap:target id="revenue-trend">↑ 12%</aap:target></small>
</div>
<div class="stat-card">
  <h3>Users</h3>
  <span class="value"><aap:target id="user-count">1,205</aap:target></span>
</div>
</aap:target>

<aap:target id="users-table">
<table>...</table>
</aap:target>
```

### 3.3 Version Chain

Every artifact maintains a version chain. Version numbers are monotonically increasing integers starting at 1. For any `edit` operation, the apply engine validates that the stored version equals `version - 1` (optimistic concurrency). If the stored version does not match, the operation is rejected as a conflict.

```
v1 (synthesize) -> v2 (edit) -> v3 (edit) -> v4 (synthesize)
```

A `name: "synthesize"` envelope resets the chain — no version validation is required.

---

## 4. Operations

The `name` field declares what the envelope represents and how `content` items are shaped. Producers SHOULD select the most token-efficient operation for the change at hand.

### 4.1 Synthesize (`name: "synthesize"`)

Complete artifact content. This is the baseline — most expensive, always correct.

**When to use**: initial creation, major rewrites, or when edit overhead exceeds content size.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `body` | string | YES | Full artifact content |

```json
{
  "protocol": "aap/0.1",
  "id": "report-42",
  "version": 1,
  "name": "synthesize",
  "meta": {"format": "text/html"},
  "content": [
    {
      "body": "<html><body><aap:target id=\"summary\"><h1>Q4 Report</h1></aap:target>...</body></html>"
    }
  ]
}
```

### 4.2 Edit (`name: "edit"`)

Express changes as operations against the previous version. Each `content` item is an edit operation applied sequentially. If any operation fails, the entire envelope is rejected and the artifact remains unchanged (all-or-nothing).

**When to use**: small, localized changes (value updates, insertions, deletions).

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `op` | string | YES | `"replace"`, `"insert_before"`, `"insert_after"`, `"delete"` |
| `target` | object | YES | Target union (see below) |
| `content` | string | no | New content (required for `replace`, `insert_before`, `insert_after`) |

#### Target Union

A target identifies where in the artifact the operation applies. The target is a discriminated union with exactly two addressing modes:

| Type | Shape | Description |
|---|---|---|
| ID | `{"type": "id", "value": "target-id"}` | Target a named `<aap:target>` marker by ID **(recommended)** |
| Pointer | `{"type": "pointer", "value": "/path/to/value"}` | Target a value by JSON Pointer (RFC 6901) — for `application/json` and `application/yaml` formats |

**ID targeting** is the recommended mode. The init context places `<aap:target id="...">` markers on updatable regions; the maintain context references them by ID. The apply engine locates the marker and operates on the content between `<aap:target id="ID">` and its closing `</aap:target>`. For `replace`, the content between markers is replaced. For `delete`, the content between markers is removed (markers are preserved). For `insert_before`, new content is inserted at the start of the range (after the opening marker). For `insert_after`, new content is inserted at the end of the range (before the closing marker). Markers themselves are never moved or removed by edit operations.

**Insertion example** (given artifact content):

```html
<aap:target id="list">item1, item2</aap:target>
```

An `insert_after` on target `list` with content `, item3` produces:

```html
<aap:target id="list">item1, item2, item3</aap:target>
```

An `insert_before` on target `list` with content `item0, ` produces:

```html
<aap:target id="list">item0, item1, item2</aap:target>
```

**Pointer targeting semantics:**
- `replace`: `content` MUST be a valid JSON value. Replaces the value at the pointer location.
- `delete`: Removes the key from an object or the element from an array (shifting subsequent indices).
- `insert_before` / `insert_after`: The pointer MUST reference an array element (last segment must be a non-negative integer). Inserts the new value before/after that index.
- Non-existent paths MUST produce an error. Pointer operations do not auto-create intermediate paths.
- Re-serialization may alter original formatting and comments.

**Example** (update two stat card values by ID):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 2,
  "name": "edit",
  "meta": {"format": "text/html"},
  "content": [
    {
      "op": "replace",
      "target": {"type": "id", "value": "revenue-value"},
      "content": "$15,720"
    },
    {
      "op": "replace",
      "target": {"type": "id", "value": "user-count"},
      "content": "1,342"
    }
  ]
}
```

**Example** (update a JSON config value by pointer):

```json
{
  "protocol": "aap/0.1",
  "id": "app-config",
  "version": 3,
  "name": "edit",
  "meta": {"format": "application/json"},
  "content": [
    {
      "op": "replace",
      "target": {"type": "pointer", "value": "/database/host"},
      "content": "\"prod-db.example.com\""
    }
  ]
}
```

---

## 5. Reprovisioning

Reprovisioning is the act of updating an existing artifact. The producer selects a strategy based on the scope of change.

### 5.1 Target-First Generation (Recommended)

Producers SHOULD emit `<aap:target>` markers on the **initial synthesize**. This incurs a small overhead (~2% extra tokens for markers) but enables all subsequent updates to use ID-based `edit` operations — reducing **output tokens** by 90–99% per update compared to full regeneration. Actual dollar savings depend on the model's output/input price ratio (see [Section 7.1.1](#711-cost-model)).

**Rationale**: the upfront cost of markers is amortized across every future update. After just one ID-targeted edit, the total output token spend is lower than two full regenerations.

> **Structural hints:** Producers SHOULD annotate structurally constrained targets with the `accepts` field — for example, table targets that expect `<tr>` children, list targets that expect `<li>` items, or code block targets that expect specific syntax. This reduces silent structural corruption when the maintain context produces replacement content. See [Section 7.2](#72-handle-name-handle) for the target info schema.

**Output cost model** ($N$ = number of future updates, $S$ = artifact size in output tokens):
- Without targets: $N$ full regenerations = $N \times S$ output tokens
- With targets: 1 synthesize (with markers) + $N$ targeted edits = $S \times 1.02 + N \times \text{edit\_tokens}$ output tokens
- Break-even: 1 update ($\text{edit\_tokens}$ is typically 1–10% of $S$)

> **Note:** Input costs are roughly equal in both cases — the maintain context reads the full artifact regardless of operation type. The savings concentrate on the output side, where tokens are 3–5x more expensive. See [Section 7.1](#71-memory-model) for the full cost derivation.

### 5.2 Strategy Selection Guide

| Change scope | Recommended operation | Output token reduction |
|---|---|---|
| Single value change | `edit` (id targeting) | ~95–99% |
| Few values changed | `edit` (id targeting) | ~90–98% |
| One section rewritten | `edit` (replace on section target) | ~80–95% |
| JSON field update | `edit` (pointer targeting) | ~95–99% |
| Complete rewrite | `synthesize` | 0% (baseline) |

> **Interpreting the table:** the "Output token reduction" column measures how many fewer output tokens the LLM produces compared to full regeneration. Because output tokens are priced 3–5x higher than input tokens (varies by provider), a 95% output reduction translates to roughly 75–80% total cost reduction when input costs are included. See [Section 7.1.1](#711-cost-model) for the precise formula.

### 5.3 Version Chain Integrity

1. Each `edit` envelope MUST have `version` equal to `stored_version + 1`
2. The apply engine MUST verify this before applying
3. On mismatch: reject the operation, notify the producer of the current version
4. The producer SHOULD re-derive its update against the correct version

### 5.4 Rollback

Consumers SHOULD maintain a configurable version history (default: 10 versions). Rollback replaces the current content with a previous version and increments the version number.

---

## 6. Token Reporting

Envelopes SHOULD include `meta.tokens_used` — the actual content tokens consumed to produce the payload. This enables consumers to track token efficiency over time.

- **Content tokens**: tokens in the artifact payload (what the user sees)
- **Overhead tokens**: envelope JSON structure, framing — excluded from the count
- Producers SHOULD select the most token-efficient operation for the change at hand

---

## 7. Artifact Type Interface

When agents manage artifacts through conversation, three costs compound: **context bloat** (KV cache grows with edit history), **token waste** (content written twice — once to read, once to regenerate), and **hallucination** (agents "remember" content they no longer have in context). The Artifact Type Interface eliminates all three by defining a contract built on two principles:

1. **The artifact is the only persistent state.** Between edits, everything is discarded — system prompts, messages, envelope operations. Only the artifact revision survives.
2. **The AI dispatches; the CPU splices.** Envelope operations (edits) are produced by a secondary context and resolved by the apply engine deterministically, at zero token cost. Content is never written twice.

### Context Offloading

The core architectural principle is **context offloading**: the orchestrator delegates artifact operations to **ephemeral secondary contexts** and remains completely unaware of artifact content. It provides a mechanism — a tool call, API, subprocess, or any invocable interface — through which operations are dispatched. The secondary context loads the artifact, processes the instruction, returns a result (a handle or handle result), and terminates. The orchestrator never sees the artifact body; it only sees the structured responses that come back through the mechanism it provided.

This is the abstraction that saves context: the orchestrator can create artifacts (via init), request edits, and receive confirmations — all without the artifact content ever entering its context window. Even initial generation is offloaded: the orchestrator passes creation instructions to an init context and receives a handle back. The mechanism is the boundary. Everything behind it is invisible to the orchestrator.

Artifact storage is implementation-specific — the artifact can live anywhere (database, file system, object store, in-memory). What matters is that the secondary context can load it for the duration of an operation. The orchestrator holds only handles and operates through the mechanism.

A secondary context is any ephemeral execution scope that is invoked with a bounded input (artifact + instruction), produces a structured output (an envelope), and terminates. The mechanism for invoking it can be anything:

- A tool call that triggers an LLM inference with a fresh context window
- A tool call to a different, cheaper model than the orchestrator
- An API request to an external service
- A subprocess or function invocation
- The same model with different parameters (temperature, system prompt)

The protocol defines two **roles** for these secondary contexts — what they do, not what they are:

- **Init context** — specialized for creation. Takes generation instructions, produces `name: "synthesize"` envelopes with well-placed targets. Runs once per artifact (or on re-initialization). After completion, context is discarded.
- **Maintain context** — specialized for reading existing content and producing edits. Receives artifact + message, produces `name: "edit"` envelopes. Context per call: `[system prompt] + [artifact vN] + [message]`. Discarded after each call. This is the key design: all edits after init go through the handle, and the secondary context stays at artifact + message — increasing recall by keeping context small and focused.
- **Apply engine** — deterministic code (not an LLM). Signature: `f(artifact, operation) -> (artifact, handle)`. Receives envelopes, resolves them against stored artifacts (~2us, 0 tokens), validates operations, stores new revisions. The artifact is stored (never seen by the orchestrator); the handle is returned.

These roles are separate because they have fundamentally different computational requirements. The init context is *generative* — it creates structure, places target boundaries, produces layout. This benefits from more capable, larger models. The maintain context is *surgical* — it reads existing content and produces minimal structured edits. This requires only high recall (find the right location in the artifact) and structured output (emit valid envelope JSON). Smaller, cheaper models excel at this constrained task.

This asymmetry is where the second dimension of cost savings emerges. AAP reduces the *number* of output tokens (edits instead of full regeneration), but context offloading also reduces the *cost per token* — the maintain context can run on a model that costs a fraction of what the orchestrator or init context uses. The two effects multiply: fewer tokens x cheaper tokens.

```
Orchestrator (handles, user conversation)
    |
    |-- create --> Init context --> name:"synthesize" envelope --> Apply engine --> Store --> name:"handle"
    |
    |-- edit --> Maintain context --> name:"edit" envelope --> Apply engine --> Store --> name:"handle"
```

> **Non-normative note:** A common realization is two LLM agents with different system prompts, models, and temperature settings behind tool-call interfaces. But the architecture is not prescriptive about mechanism. Any implementation where the orchestrator provides a mechanism to dispatch operations to ephemeral secondary contexts — and those contexts operate on less data than the orchestrator holds — is compliant.

Because the artifact is a concrete, standalone piece of content (an HTML file, a Python module, a config), it can also be interacted with directly — outside any orchestrator context. A user can open it in a browser, edit it by hand, or load it into a fresh LLM context for fine-tuning. This is particularly useful for iterative refinement: abandon the orchestrator, work with the artifact directly in a dedicated context, then resume protocol-managed operations by re-registering the modified artifact as a new version. The protocol's version chain accommodates this — a `name: "synthesize"` envelope resets the chain without requiring continuity from the previous version.

### 7.1 Memory Model

Each secondary context invocation is a **stateless dispatch** — an independent call with no conversation history. The artifact is the single source of truth.

**Init context (runs once):**

```
[Instructions (creation-specialized)] + [Generation prompt]
                    | produces |
[name:"synthesize" envelope with targets]
                    | apply engine (CPU) |
[Artifact v1] <- stored, context discarded
[Handle] <- returned to orchestrator
```

**Maintain context (runs per edit):**

```
[Instructions (maintenance-specialized)] + [Artifact vN] + [Message]
                    | produces |
[name:"edit" envelope with operations]
                    | apply engine (CPU) |
[Artifact vN+1] <- stored, context discarded
[Handle] <- returned to orchestrator
```

In every case: instructions are re-injected next time. The message is discarded. Envelope operations are consumed by the apply engine and discarded. Previous edits never existed in the current context. Only the artifact persists.

**Normative requirements:**

- The orchestrator MUST expose a mechanism (tool calls, API dispatch, or equivalent) through which it can operate on artifact handles — creating and editing artifacts via secondary context invocations
- Implementations MUST NOT accumulate edit history in any secondary context
- Each invocation MUST start with a fresh context
- The maintain context MUST produce `edit` envelopes — the apply engine resolves them against the stored artifact
- The maintain context SHOULD NOT produce `name: "synthesize"` envelopes on edits — this defeats the model by writing content tokens twice
- The init context SHOULD produce artifacts with targets ([Section 5.1](#51-target-first-generation-recommended)) to enable efficient subsequent edits
- The artifact content is the single source of truth, not conversation memory

#### 7.1.1 Cost Model

The cost of artifact operations depends on three LLM-specific variables that vary across providers and models:

| Variable | Definition | Typical range |
|---|---|---|
| $S_k$ | Artifact size in tokens at version $k$ (tokenizer-dependent) | 500–10,000 |
| $d_k$ | Edit envelope size in output tokens for edit $k$ | 30–500 |
| $I$ | System prompt + instructions in tokens | 200–1,000 |
| $p_{\text{in}}$ | Price per input token | varies by model |
| $p_{\text{out}}$ | Price per output token | varies by model |
| $r$ | Output/input price ratio ($p_{\text{out}} / p_{\text{in}}$) | 1–5x |
| $N$ | Number of edits over the artifact's lifetime | $1$–$\infty$ |

> **Why these variables matter:** A given 8 KB HTML artifact might tokenize to ~2,000 tokens on GPT-4's tokenizer but ~2,400 on Claude's. The output/input price ratio ranges from 1x (some open-source providers) to 5x (frontier models). These differences change the absolute savings but not the structural advantage — AAP always reduces output tokens, and output tokens are always $\geq$ input token price.

##### Three Scenarios

To understand where savings come from, compare three approaches to making $N$ edits on an artifact. The formulas use $S_k$ for artifact size at version $k$ and $d_k$ for edit envelope size at edit $k$.

**Scenario A — Naive conversation (single growing context, full regen):**

The LLM accumulates conversation history. At edit $k$, the context contains all prior versions.

| Component | Input tokens | Output tokens |
|---|---|---|
| Edit $k$ | $I + S_0 + S_1 + \ldots + S_{k-1} + \text{messages}$ | $S_k$ |
| Total ($N$ edits) | $N \cdot I + \sum_{j=0}^{N-1} (N-j) \cdot S_j$ | $\sum_{k=0}^{N} S_k$ |

Input cost grows **superlinearly** — each prior version is re-read in every subsequent turn. When $S_k$ is stable, this simplifies to $O(N^2 \cdot S)$.

**Scenario B — Stateless full regen (fresh context, full output):**

Each edit starts a fresh context with the current artifact, but the LLM still regenerates the full content.

| Component | Input tokens | Output tokens |
|---|---|---|
| Edit $k$ | $I + S_{k-1} + \text{message}$ | $S_k$ |
| Total ($N$ edits) | $\sum_{k=0}^{N} (I + S_k)$ | $\sum_{k=0}^{N} S_k$ |

Input cost is **linear** in $N$ — context offloading eliminates the superlinear growth. But output cost is unchanged: the LLM regenerates the full artifact every time.

**Scenario C — AAP (fresh context, edit output):**

Each edit starts a fresh context. The LLM reads the full artifact but produces only an edit envelope.

| Component | Input tokens | Output tokens |
|---|---|---|
| Init (create) | $I + \text{prompt}$ | $S_0$ |
| Edit $k$ | $I + S_{k-1} + \text{message}$ | $d_k$ |
| Total ($N$ edits) | $I + \sum_{k=1}^{N} (I + S_{k-1})$ | $S_0 + \sum_{k=1}^{N} d_k$ |

Input cost is **identical to Scenario B** (both read the current artifact per edit). Output cost drops from $\sum S_k$ to $S_0 + \sum d_k$. Since $d_k \ll S_k$ for targeted edits, this is the primary savings.

##### Where the Savings Come From

The fundamental trade: **spend input tokens to read the artifact, produce a small edit as output, and let the CPU apply it.** The edit output is consumed by the deterministic apply engine — it never re-enters any LLM context. Meanwhile, the orchestrator (the main conversation) never reads the artifact at all; it holds only lightweight handles. This architecture produces three independent, compounding savings.

**Effect 1 — Output tokens are consumed, not re-read (C vs B).**

In Scenario B (stateless full regen), every edit produces $S_k$ output tokens — the full artifact, regenerated. Those $S_k$ tokens are the product, but producing them is the expensive part: output tokens cost $r \times$ more than input tokens.

In Scenario C (AAP), the LLM produces $d_k$ tokens — an edit envelope describing what changed. The apply engine resolves the edit against the stored artifact deterministically (CPU, ~2μs, zero tokens) and stores the new version. The $d_k$ output tokens are **consumed by the apply engine and discarded** — no LLM ever reads them back as input.

The maintain context does re-read the full artifact ($S_{k-1}$ input tokens) each edit — that's how it knows what to edit. But input tokens are cheap ($1/r$ of the output price). The trade is always profitable: pay $S_{k-1} \cdot p_{\text{in}}$ to read, save $(S_k - d_k) \cdot p_{\text{out}}$ on output. Since $r \geq 1$ and $d_k \ll S_k$, the output savings dominate.

**Effect 2 — The orchestrator never reads the artifact (context separation).**

In a naive conversation (Scenario A), the main context holds the full artifact — and every prior version. Each regeneration ($S_k$ output tokens) becomes part of the context for the next edit ($S_k$ input tokens). You write $S_0$, it gets read back next turn, you write $S_1$ on top of it, and now the following turn reads $S_0 + S_1$. Every output $S_j$ paid in round $j$ is paid again as input in rounds $j+1, j+2, \ldots, N$. This is the mechanism behind superlinear growth.

AAP eliminates this through **context separation**:

- The **orchestrator** (main context) holds only handles (~10 tokens). It never reads the artifact body. Its context grows only with conversation, not with artifact size.
- The **maintain context** is ephemeral — it loads the current artifact revision ($S$ tokens), produces an edit ($d$ tokens), and terminates. Its context is discarded after each call.
- The **apply engine** is pure CPU. It consumes the edit envelope, splices it into the stored artifact, and stores the new version.

A crucial distinction: the maintain context *does* read the applied result of all prior edits — the artifact at version $k$ reflects every edit that was ever applied. But it reads only the **current artifact** ($S_k$ tokens), not the **edit history** (all prior envelopes, conversations, and regenerations). The edit envelope itself ($d$ tokens) is consumed by the apply engine and never re-enters any LLM context. What the maintain context sees is the *product* of prior edits, not the *process*.

Note that $S_k$ (artifact size at version $k$) is not fixed — it may grow if an operation adds content, or shrink if content is deleted. In the cost formulas, $S$ represents the artifact size at the time of each edit. The key property is that $S_k$ depends only on the artifact's content, not on the number of prior edits or the size of prior conversations. In a naive conversation, context at edit $k$ is proportional to $k \cdot S$ (all prior versions); in AAP, input at edit $k$ is always $I + S_k$ — bounded by the artifact's current size, not its history.

The input savings (A→C) over $N$ edits:

$$\text{Input}_A - \text{Input}_C = \sum_{j=0}^{N-1} (N-j) \cdot S_j - \sum_{k=1}^{N} (I + S_{k-1})$$

When $S_k$ is roughly stable ($S_k \approx S$), this simplifies to $\sim S \cdot N^2 / 2$ — quadratic in $N$. The longer the artifact lives, the more AAP saves on input *in addition to* saving on output.

**Effect 3 — Model cost asymmetry.** The maintain context (which produces edits) can run on a cheaper model than the orchestrator or init context. A small model with good recall and structured output is sufficient for producing edits against content it can see in full. If the maintain model costs $c_m$ per output token and the init/orchestrator model costs $c_o$, the effective per-edit output cost is $d_k \cdot c_m$ instead of $S_k \cdot c_o$.

These effects multiply: **fewer output tokens $\times$ cheaper per token $\times$ no context accumulation.**

##### Per-Edit Cost Comparison

The **total cost** of a single edit (init excluded) under each scenario. Edit $k$ (1-indexed):

| | Input cost (edit $k$) | Output cost (edit $k$) | Total (edit $k$) |
|---|---|---|---|
| **A (naive convo)** | $(I + \sum_{j<k} S_j) \cdot p_{\text{in}}$ | $S_k \cdot p_{\text{out}}$ | $(I + \sum_{j<k} S_j) \cdot p_{\text{in}} + S_k \cdot p_{\text{out}}$ |
| **B (stateless full)** | $(I + S_{k-1}) \cdot p_{\text{in}}$ | $S_k \cdot p_{\text{out}}$ | $(I + S_{k-1}) \cdot p_{\text{in}} + S_k \cdot p_{\text{out}}$ |
| **C (AAP edit)** | $(I + S_{k-1}) \cdot p_{\text{in}}$ | $d_k \cdot p_{\text{out}}$ | $(I + S_{k-1}) \cdot p_{\text{in}} + d_k \cdot p_{\text{out}}$ |

**C vs B (same input, less output):** Input costs are identical — the maintain context reads the full artifact regardless. Savings are purely on the output side: $(S_k - d_k) \cdot p_{\text{out}}$ per edit. This is the edit efficiency.

**C vs A (less input AND less output):** At edit $k$, Scenario A reads all prior artifact versions ($\sum_{j<k} S_j$) that Scenario C never sees. Input savings grow with $k$ — the longer the artifact lives, the wider the gap. Output savings $(S_k - d_k) \cdot p_{\text{out}}$ apply on top.

This is why the output/input price ratio matters: the higher $r = p_{\text{out}} / p_{\text{in}}$, the more the output reduction dominates total savings. But even at $r = 1$, AAP saves on both sides vs the naive conversation.

The **cost savings percentage** for a single edit (B→C), using $S$ for $S_{k-1} \approx S_k$ and $d$ for $d_k$:

$$\text{savings\%} = \frac{(S - d) \cdot p_{\text{out}}}{(I + S) \cdot p_{\text{in}} + S \cdot p_{\text{out}}} = \frac{(S - d) \cdot r}{(I + S) + S \cdot r}$$

Where $r = p_{\text{out}} / p_{\text{in}}$. As $r \to \infty$, $\text{savings\%} \to (S - d) / S \approx 1$ (approaches the raw output token reduction). As $r \to 1$, $\text{savings\%} \approx (S - d) / (I + 2S)$ (approaches roughly half the output reduction, since input and output cost equally).

> **Non-normative note:** The $d_k \approx 30\text{–}500$ output token estimate is derived from hand-crafted envelope benchmarks. AI-generated envelopes from natural language messages may produce larger edits or fall back to section-level rewrites when a targeted edit would suffice. Implementations SHOULD track actual output token counts to calibrate expectations.

#### 7.1.2 Amortization

The initial creation (init context, `name: "synthesize"`) is the most expensive operation — full output tokens to produce the artifact with targets. This is a one-time investment that makes every subsequent edit cheap.

##### Iteration-by-Iteration Comparison

Total **cumulative cost** after each edit (init + N edits):

| | Init | After 1 edit | After 5 edits | After 10 edits |
|---|---|---|---|---|
| **A (naive convo)** input | $I$ | $I + (I+S)$ | $I + 5I + 15S$ | $I + 10I + 55S$ |
| **A** output | $S$ | $2S$ | $6S$ | $11S$ |
| **B (stateless full)** input | $I$ | $I + (I+S)$ | $I + 5(I+S)$ | $I + 10(I+S)$ |
| **B** output | $S$ | $2S$ | $6S$ | $11S$ |
| **C (AAP)** input | $I$ | $I + (I+S)$ | $I + 5(I+S)$ | $I + 10(I+S)$ |
| **C** output | $S$ | $S + d$ | $S + 5d$ | $S + 10d$ |

The output rows tell the story. After $N$ edits:

- **B and A** produce $(N+1) \cdot S$ output tokens
- **C** produces $S + N \cdot d$ output tokens
- **Output savings** = $N \cdot (S - d)$ tokens

##### Concrete Example

An 8 KB HTML dashboard artifact with typical model pricing:

| Parameter | Value | Rationale |
|---|---|---|
| $S$ | 2,000 tokens | ~4 bytes/token average for HTML |
| $d$ | 30 tokens | Small edit: update two stat values |
| $I$ | 500 tokens | System prompt + AAP instructions |
| $r$ ($p_{\text{out}}/p_{\text{in}}$) | 4x | Typical frontier model ratio |
| $N$ | 10 edits | Moderate lifecycle |

**Output tokens (cumulative):**

| Edit # | B: Stateless full | C: AAP edit | C saves |
|---|---:|---:|---:|
| Init | 2,000 | 2,000 | 0 |
| 1 | 4,000 | 2,030 | 1,970 |
| 2 | 6,000 | 2,060 | 3,940 |
| 5 | 12,000 | 2,150 | 9,850 |
| 10 | 22,000 | 2,300 | 19,700 |

**Dollar cost (output only, at \$15/M output tokens):**

| Edit # | B output cost | C output cost | C saves |
|---|---:|---:|---:|
| Init | \$0.030 | \$0.030 | \$0.000 |
| 1 | \$0.060 | \$0.030 | \$0.030 |
| 5 | \$0.180 | \$0.032 | \$0.148 |
| 10 | \$0.330 | \$0.035 | \$0.296 |

**Dollar cost (total: input + output, at \$3.75/M input, \$15/M output):**

| Edit # | A (naive convo) | B (stateless full) | C (AAP edit) | C vs B saves | C vs A saves |
|---|---:|---:|---:|---:|---:|
| Init | \$0.032 | \$0.032 | \$0.032 | 0% | 0% |
| 1 | \$0.071 | \$0.069 | \$0.039 | 43% | 45% |
| 5 | \$0.304 | \$0.217 | \$0.070 | 68% | 77% |
| 10 | \$0.763 | \$0.402 | \$0.107 | 74% | 86% |

The three columns reveal the two savings mechanisms:

- **B vs A** (input savings from context flattening): \$0.763 → \$0.402 at edit 10. The naive conversation re-reads every prior regeneration; stateless dispatch reads only the current version.
- **C vs B** (output savings from edit operations): \$0.402 → \$0.107 at edit 10. Same input cost, but output drops from $S$ to $d$ per edit.
- **C vs A** (both effects combined): \$0.763 → \$0.107 at edit 10 — **86% total savings**. The gap widens with every edit because both quadratic input growth *and* redundant output accumulate in A but not in C.


> **Sensitivity to price ratio:** At $r = 1$ (equal input/output pricing), the same scenario yields ~49% total savings after 10 edits. At $r = 5$, it reaches ~78%. The output token reduction is constant regardless — what changes is how much of total cost it represents.

##### With Model Asymmetry

If the maintain context runs on a model costing 1/10th the orchestrator's output price (e.g., a small model for structured edits), the output cost column for C drops further. In the example above, 10 edits of AAP edit output at 1/10th price: \$0.035 × 0.1 = \$0.0035 — effectively free. Total savings approach the theoretical maximum.

##### Break-Even

Break-even occurs at **one edit**. After a single edit update, cumulative output spend ($S + d$) is less than two full regenerations ($2S$) whenever $d < S$ — which is always true for any non-trivial artifact.

#### 7.1.3 Why Savings Are LLM-Dependent

The three variables that determine actual dollar savings are all model-specific:

**Tokenizer efficiency.** The same 8 KB HTML file tokenizes to different counts across models. Byte-pair encoding (BPE) tokenizers average 3–4 bytes/token for English prose but vary for code, markup, and non-Latin scripts. $S_k$ (artifact size in tokens) is not a fixed number — it depends on both the model and the artifact's current content. However, $d_k / S_k$ (the ratio of edit to full) is relatively stable across tokenizers because both numerator and denominator scale similarly.

**Output/input price ratio ($r$).** This is the single most important factor for translating output token reduction into dollar savings. At $r = 5$, output tokens dominate cost and AAP captures most of the total. At $r = 1$, output and input cost equally and AAP captures roughly half.

| $r$ ($p_{\text{out}}/p_{\text{in}}$) | Output % of edit cost (no AAP) | AAP total savings % ($d/S = 1.5\%$) |
|---|---:|---:|
| 1x | 44% | ~43% |
| 2x | 62% | ~60% |
| 3x | 71% | ~69% |
| 4x | 76% | ~74% |
| 5x | 80% | ~78% |

**Model cost per token.** The maintain context does not require a frontier model — it needs recall (find the right location in the artifact) and structured output (emit valid envelope JSON). Smaller, cheaper models excel at this constrained task. When the maintain model is cheaper than the orchestrator, the savings multiply beyond what output token reduction alone provides.

> **Non-normative note:** Implementations SHOULD report both output token reduction (model-independent) and estimated cost savings (model-dependent) in their benchmarks. Payload byte reduction (as measured by the Rust apply engine) is a useful proxy for output token reduction but not identical — envelope JSON overhead adds a small constant.

#### 7.1.4 Anti-Hallucination Properties

The architecture structurally reduces hallucination through context separation:

- The **orchestrator** never sees full artifact content. It holds only handles. It can describe *intent* but cannot hallucinate *content* it has never seen.
- The **init context** produces content from instructions — hallucination risk is inherent to generation, but its context is clean.
- The **maintain context** sees the *actual current revision*, injected fresh from storage. It produces edits against real content, not imagined content.
- The **apply engine** is deterministic code. It either applies the operations correctly or returns an error.

> **Non-normative note:** The maintain context *can* still hallucinate envelope operations — for example, targeting an ID that doesn't exist. However, the risk is structurally lower because: (1) the context contains *only* the artifact and the message; (2) the apply engine validates operations deterministically; (3) the artifact is always smaller than a full conversation thread. Implementations SHOULD track hallucination rates to monitor quality.

### 7.2 Handle (`name: "handle"`)

A **handle** is an envelope the orchestrator holds instead of full artifact content. It is returned after every `synthesize` or `edit` operation. It provides enough metadata for decision-making without consuming context budget.

The handle contains the artifact's identity and optional metadata. Implementations MAY include the `content` field when the orchestrator explicitly requests the artifact body (e.g., to answer a user's question), but by default handles are lightweight.

**Content item schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | YES | Artifact identifier |
| `version` | integer | YES | Current artifact version |
| `token_count` | integer | no | Approximate token count of the full artifact |
| `state` | string | no | Entity lifecycle state |
| `content` | string | no | Artifact body (included only when explicitly requested) |
| `targets` | array | no | List of valid target IDs in the current artifact (see target info schema below) |

> **Note:** The `id` and `version` fields in handle content items intentionally duplicate the envelope-level fields. This allows handle content items to be extracted and used standalone — for example, when an orchestrator maintains a collection of handles independent of their original envelopes.

**Target info schema** (items of `targets` array):

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | YES | Target identifier (matches `<aap:target id="...">` in the artifact) |
| `label` | string | no | Human-readable description of the target's purpose |
| `accepts` | string | no | Hint about valid replacement content (e.g., `"tr*"` for table rows, `"li*"` for list items) |

The `targets` array transforms targeting from a recall problem (the maintain context must remember IDs from the artifact it read) into a selection problem (the maintain context picks from a closed list). This eliminates the dominant failure mode of hallucinated target IDs.

The `accepts` field is a structural hint for the maintain context — not enforced by the apply engine. Init contexts SHOULD annotate structurally constrained targets (tables, lists, select options, code blocks) with what valid replacement content looks like.

**Example:**

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 5,
  "name": "handle",
  "meta": {"format": "text/html", "state": "published"},
  "content": [
    {
      "id": "dashboard-001",
      "version": 5,
      "token_count": 10240,
      "targets": [
        {"id": "stats", "label": "Statistics section"},
        {"id": "revenue-value"},
        {"id": "user-count"},
        {"id": "users-table", "label": "Users data table", "accepts": "tr*"}
      ]
    }
  ]
}
```

### 7.3 Error Recovery

When the maintain context produces a bad edit — for example, targeting an ID that doesn't exist — the apply engine rejects the operation and returns an error.

**Apply engine error object:**

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | string | YES | Machine-readable error code (see table below) |
| `message` | string | YES | Human-readable description |
| `artifact_id` | string | no | Artifact that triggered the error |

**Error codes:**

| Code | Description |
|---|---|
| `version_conflict` | `version` does not equal `stored_version + 1` |
| `target_not_found` | A referenced target ID or JSON Pointer does not exist in the artifact |
| `invalid_envelope` | Envelope failed structural validation (missing fields, wrong types) |
| `invalid_content` | Content items failed operation-specific validation |

> **Note:** Transport-level errors (timeouts, budget exhaustion, reconnection) are defined separately in the [SSE transport binding](aap-sse.md#5-error-signaling).

**Recommended recovery flow:**

1. Orchestrator reads the error from the apply engine
2. Orchestrator reformulates the edit with more specific context
3. Retry with the maintain context
4. If repeated failures, escalate to re-initialization: archive the current artifact and call the init context

> **Restructuring:** When an artifact's target topology is fundamentally inadequate, the recommended approach is to archive the existing artifact and create a new one via the init context. There is no in-place restructuring operation — restructuring is creation.

### 7.4 Target Recomputation

After any `synthesize` or `edit` operation, the apply engine MUST derive the target list from the resulting artifact content. The handle's `targets` array reflects the current artifact state, not the previous handle's targets.

**Normative requirements:**

- The apply engine MUST scan the artifact body for `<aap:target id="...">` markers after every operation and populate the handle's `targets` array
- When a `replace` operation targets a parent that contains nested targets, the nested targets are invalidated if the replacement content does not contain them
- The returned handle MUST NOT include target IDs that no longer exist in the artifact body
- If the replacement content introduces new `<aap:target>` markers, those MUST appear in the returned handle's targets
- Orchestrators MUST use the latest handle's target list when injecting target information into the maintain context

> **Non-normative note:** This ensures the maintain context always operates on a closed, valid target set. When the orchestrator injects the handle's `targets` into the maintain context's prompt, the model selects from known-good IDs rather than recalling them from artifact text — collapsing the dominant failure mode of hallucinated target IDs.

### 7.5 Operations Summary

The Artifact Type Interface defines two operations, both returning a handle:

| Operation | Input | Output | Description |
|---|---|---|---|
| `synthesize` | `name: "synthesize"` | `name: "handle"` | Create or recreate artifact, return handle |
| `edit` | `name: "edit"` | `name: "handle"` | Apply targeted changes, return updated handle |

**Normative:** Orchestrators MUST use handles to interact with artifacts. The orchestrator never holds full artifact content; it dispatches through handles.

---

## 8. Artifact Entity State

Artifacts can optionally be treated as **managed entities** with lifecycle states, ownership, relationships, and expiration. All entity fields are optional — Level 0-1 consumers ignore them.

### 8.1 State Machine

```
              publish           archive
  +---------+ ------> +-----------+ ------> +----------+
  |  draft   |         | published  |         | archived  |
  +---------+ <------ +-----------+         +----------+
              unpublish          restore
                                  <------------------------
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

State is carried in the `meta.state` field.

### 8.2 Entity Metadata

The optional `entity` object holds ownership and organizational metadata. Entity metadata is carried outside the handle envelope by the platform layer — the handle itself is kept minimal (see [Section 7.2](#72-handle-name-handle)).

| Field | Type | Required | Description |
|---|---|---|---|
| `owner` | string | no | Owning user or system identifier |
| `created_by` | string | no | Creator identifier |
| `tags` | array of strings | no | Freeform classification tags |
| `permissions` | object | no | Access control (see [Section 8.3](#83-permissions)) |
| `collection` | string | no | Workspace or collection grouping identifier |
| `ttl` | integer | no | Time-to-live in seconds from last update |
| `expires_at` | string | no | ISO 8601 expiration timestamp (takes precedence over `ttl`) |
| `relationships` | array | no | Links to other artifacts (see [Section 8.4](#84-relationships)) |

**Example** (handle envelope with entity metadata):

```json
{
  "protocol": "aap/0.1",
  "id": "dashboard-001",
  "version": 3,
  "name": "handle",
  "meta": {"format": "text/html", "state": "published"},
  "content": [
    {
      "id": "dashboard-001",
      "version": 3,
      "token_count": 10240,
      "state": "published"
    }
  ]
}
```

> **Non-normative note:** Entity metadata (ownership, tags, permissions, relationships) is carried outside the handle envelope by the platform layer. The handle itself is kept minimal — only the fields needed for the orchestrator to make decisions.

### 8.3 Permissions

The `permissions` object uses a role-based model:

| Field | Type | Description |
|---|---|---|
| `read` | array of strings | Principals that can read the artifact |
| `write` | array of strings | Principals that can update the artifact |
| `admin` | array of strings | Principals that can change state, permissions, and delete |

Principal identifiers follow the format `<type>:<id>` (e.g., `"user:alice"`, `"team:finance"`, `"agent:claude"`, `"*"` for public). Enforcement is outside protocol scope — this is metadata for the platform to act on.

### 8.4 Relationships

Artifacts can declare typed relationships:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | YES | Relationship type: `"depends_on"`, `"parent"`, `"child"`, `"derived_from"`, `"supersedes"`, `"related"` |
| `target` | string | YES | Target artifact ID |
| `version` | integer | no | Specific version of the target (omit for latest) |

Relationships are informational. Consumers MAY use them for dependency resolution but MUST NOT require them for correct envelope processing.

### 8.5 Optimistic Locking

The `version` field provides optimistic concurrency control. For `edit` operations, the apply engine validates `stored_version == version - 1`. State transitions follow the same rule.

For advisory (non-mandatory) locking, an optional `lock` object may be included in `content`:

| Field | Type | Description |
|---|---|---|
| `held_by` | string | Principal holding the lock |
| `acquired_at` | string | ISO 8601 timestamp |
| `ttl` | integer | Lock duration in seconds (auto-releases after expiry) |

Advisory locks are hints only. The version mechanism remains the authoritative concurrency control.

### 8.6 TTL and Expiration

- When `ttl` is set, the artifact expires `ttl` seconds after its last update
- When `expires_at` is set, it takes precedence over `ttl`
- Expired artifacts SHOULD transition to `"archived"` state automatically
- Consumers SHOULD check expiration on read and treat expired artifacts as archived

---

## 9. Conformance Levels

Implementations declare their conformance level. Each level is a superset of the previous.

### Level 0 — Synthesize

- MUST parse and produce valid envelopes
- MUST support `name: "synthesize"`
- MUST validate `protocol` field

### Level 1 — Edit

- Level 0, plus:
- MUST support `name: "edit"` with `id` and `pointer` targeting
- MUST maintain version chain and enforce version concurrency

### Level 2 — Managed Artifacts

- Level 1, plus:
- MUST support `name: "handle"` as the output of every synthesize and edit operation
- MUST implement the Artifact Type Interface ([Section 7](#7-artifact-type-interface)): synthesize and edit, both returning handles
- MUST support context offloading: init context for creation, maintain context for edits. The orchestrator MUST provide a mechanism (tool calls, API dispatch, subprocess invocation, or equivalent) for secondary contexts to operate on artifacts
- MUST support the stateless dispatch memory model — no edit history accumulates in any secondary context
- The maintain context MUST produce `edit` envelopes, not `synthesize`, on edits
- MUST support `meta.state` and enforce state machine transitions ([Section 8.1](#81-state-machine))
- Orchestrators MUST use handles rather than full content for artifact interaction
- MUST populate handle `targets` array derived from the current artifact state after every mutation ([Section 7.4](#74-target-recomputation))

---

## 10. Security Considerations

- **Content injection**: consumers MUST sanitize artifact content before displaying in privileged contexts (e.g., web browsers). Content display and sandboxing are consumer responsibilities outside the protocol scope
- **Checksum verification**: consumers SHOULD verify `meta.checksum` when present to detect tampering or corruption
- **Token budget enforcement**: producers MUST NOT exceed declared budgets; consumers SHOULD reject payloads that claim to use fewer tokens than they actually contain
- **Entity permissions**: `permissions` in the entity object are metadata only — consumers MUST enforce access control at the platform level, not rely solely on envelope metadata

---

## 11. IANA Considerations

This specification does not require any IANA registrations. The `meta.format` field uses existing MIME types.

---

## Appendix A: JSON Schemas

Machine-validatable schemas for all protocol structures are provided in the `schemas/` directory:

- [`artifact-envelope.json`](schemas/artifact-envelope.json) — Envelope schema (covers all 3 envelope types)
- [`artifact.json`](schemas/artifact.json) — Artifact schema (standalone content object)
- [`edit-operation.json`](schemas/edit-operation.json) — Edit operation schema (content items for `name: "edit"`)
- [`entity-metadata.json`](schemas/entity-metadata.json) — Entity metadata schema
- [`relationship.json`](schemas/relationship.json) — Artifact relationship schema

## Appendix B: Token Savings Reference

Empirical measurements from the reference implementation using a 40KB HTML dashboard artifact:

| Edit scenario | Synthesize tokens | Edit tokens | Savings |
|---|---|---|---|
| Change 1 stat value | ~10,000 | ~50 | 99.5% |
| Add 5 table rows | ~10,000 | ~300 | 97.0% |
| Update all CSS colors | ~10,000 | ~700 | 93.0% |
| Rewrite one section | ~10,000 | ~1,000 | 90.0% |

*Values are approximate; run `cargo bench --bench aap` for current apply engine measurements.*
