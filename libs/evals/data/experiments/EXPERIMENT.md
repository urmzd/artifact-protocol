# GAP Conversation Benchmark Experiment

## Hypothesis

The Generative Artifact Protocol reduces token cost and latency for multi-turn artifact editing compared to the default full-regeneration approach. Specifically:

1. **Output tokens decrease 90-99%** on edit turns (diff/section envelopes vs full artifact)
2. **Input tokens stay bounded** — GAP context does not grow with conversation history
3. **Cumulative cost breaks even after one edit** — the protocol overhead (larger system prompt) is recovered
4. **Apply engine adds negligible latency** — envelope resolution is ~2μs, dominated by LLM time
5. **Envelope reliability is measurable** — the maintain context can produce valid, applicable envelopes

## Design

### Shared Turn 0

Both flows start from the **same artifact**. The creation prompt is run once. The resulting artifact is used as the starting point for both the default and GAP edit flows. This eliminates variance in the baseline and ensures edits operate on identical content.

### Two Flows, Same Edits

Each experiment runs the same sequence of follow-up edits through both flows:

**Default flow** — single-thread conversation:
- System prompt: `"You produce {format} artifacts. Output raw code only."`
- Turn 0: creation prompt → full artifact (shared)
- Turn N: full conversation history + edit instruction → full artifact regeneration
- Context grows with every turn (prior artifacts accumulate in message history)

**GAP flow** — stateless dispatch:
- Turn 0: same creation prompt → same artifact (shared)
- Turn N: fresh maintain context call with:
  - System prompt: GAP spec excerpt (~350 tokens, describes envelope format)
  - Artifact injection: current artifact revision (not conversation history)
  - Edit instruction: same edit as default flow
  - Output: JSON envelope (diff or section operations)
  - Apply: deterministic engine resolves envelope → new artifact revision

### Controlled Variables

| Variable | Value | Rationale |
|---|---|---|
| Model | Same for both flows | Eliminates model capability differences |
| Temperature | 0 (or lowest available) | Maximizes reproducibility |
| Seed | Fixed per experiment | Deterministic where supported |
| Edit instructions | Identical text | Same task, different execution |
| Starting artifact | Shared (run once) | No variance in baseline |
| System prompt | **NOT controlled** — this IS the independent variable | The GAP system prompt is larger; this cost is the protocol overhead |

### Independent Variable

The **system prompt and conversation structure** differ between flows. This is the intervention being tested:

- Default: minimal system prompt + growing conversation context
- GAP: spec-aware system prompt + bounded artifact injection

The GAP system prompt is intentionally **not optimized** — it uses a straightforward spec excerpt, not a hand-tuned minimal prompt. This represents what a real user would start with (suboptimal prompting baseline).

### Dependent Variables (Measured)

| Metric | Unit | Per-turn | Cumulative |
|---|---|---|---|
| `input_tokens` | count | YES | YES |
| `output_tokens` | count | YES | YES |
| `llm_latency_ms` | milliseconds | YES | YES |
| `apply_latency_us` | microseconds | YES (GAP only) | YES |
| `envelope_parsed` | boolean | YES (GAP only) | success rate |
| `apply_succeeded` | boolean | YES (GAP only) | success rate |
| `output_bytes` | bytes | YES | — |

### Fairness Guarantees

1. **Shared baseline**: Turn 0 runs once and is reused. Both flows edit the same artifact.
2. **Same model + params**: Identical LLM configuration for both flows.
3. **Protocol overhead measured honestly**: The GAP system prompt's token cost is reported separately as `system_prompt_tokens`. It is NOT hidden or excluded from totals.
4. **Failures counted**: If the GAP flow produces an unparseable envelope or the apply engine rejects it, this is recorded as a failure — not silently retried or discarded.
5. **No prompt optimization**: The GAP system prompt is a naive spec excerpt. Future work can measure the impact of prompt engineering, but the baseline experiment uses the straightforward version.
6. **Sequential execution**: Both flows run sequentially (not interleaved) to avoid resource contention affecting latency measurements.

## Directory Structure

Each experiment produces:

```
{NNN}-{prompt-id}/
├── shared/
│   ├── prompt.md                    # creation prompt (identical for both)
│   └── artifact.{ext}              # turn-0 artifact (shared baseline)
├── inputs/
│   ├── default/
│   │   ├── system.md               # default system prompt
│   │   ├── turn-1.md               # full context + edit (shows growing input)
│   │   ├── turn-2.md               # full context + edit (even larger)
│   │   └── ...
│   └── gap/
│       ├── system.md               # GAP system prompt (spec excerpt)
│       ├── turn-1.md               # artifact injection + edit intent (bounded)
│       ├── turn-2.md               # artifact injection + edit intent (bounded)
│       └── ...
├── outputs/
│   ├── default/
│   │   ├── turn-1.{ext}            # full artifact (regenerated)
│   │   ├── turn-2.{ext}            # full artifact (regenerated)
│   │   └── ...
│   └── gap/
│       ├── turn-1.json             # GAP envelope (raw LLM output)
│       ├── turn-1.{ext}            # resolved artifact (after apply engine)
│       ├── turn-2.json
│       ├── turn-2.{ext}
│       └── ...
└── metrics.json                     # all measurements
```

## Metrics Schema

```json
{
  "experiment_id": "001-html-dashboard-ecommerce",
  "prompt_id": "html-dashboard-ecommerce",
  "model": "qwen3.5:4b",
  "provider": "ollama",
  "seed": 42,
  "temperature": 0,
  "timestamp": "2026-04-02T10:00:00Z",

  "shared": {
    "creation_input_tokens": 525,
    "creation_output_tokens": 10000,
    "creation_latency_ms": 45000,
    "artifact_bytes": 8192
  },

  "default_flow": {
    "system_prompt_tokens": 25,
    "per_turn": [
      {
        "turn": 1,
        "edit": "Update revenue to $215,430",
        "input_tokens": 10800,
        "output_tokens": 10200,
        "latency_ms": 48000,
        "output_bytes": 8250
      }
    ],
    "total_input_tokens": 10800,
    "total_output_tokens": 10200,
    "total_latency_ms": 48000
  },

  "gap_flow": {
    "system_prompt_tokens": 350,
    "per_turn": [
      {
        "turn": 1,
        "edit": "Update revenue to $215,430",
        "input_tokens": 10600,
        "output_tokens": 150,
        "latency_ms": 3200,
        "output_bytes": 200,
        "envelope_parsed": true,
        "apply_succeeded": true,
        "apply_latency_us": 2,
        "envelope_name": "diff",
        "envelope_ops_count": 1
      }
    ],
    "total_input_tokens": 10600,
    "total_output_tokens": 150,
    "total_latency_ms": 3200,
    "envelope_parse_rate": 1.0,
    "apply_success_rate": 1.0
  },

  "comparison": {
    "output_token_savings_pct": 98.5,
    "input_token_savings_pct": 1.9,
    "latency_savings_pct": 93.3,
    "break_even_turn": 1,
    "protocol_overhead_tokens": 325,
    "protocol_overhead_amortized_by_turn": 1
  }
}
```

### Comparison Fields

- `output_token_savings_pct`: `(default_out - gap_out) / default_out * 100`
- `input_token_savings_pct`: `(default_in - gap_in) / default_in * 100` — may be negative on turn 1 (GAP system prompt is larger) but positive on later turns (default context grows)
- `break_even_turn`: the turn at which GAP's cumulative total tokens first dip below default's
- `protocol_overhead_tokens`: `gap_system_prompt_tokens - default_system_prompt_tokens` — the fixed cost of teaching the LLM the protocol
- `protocol_overhead_amortized_by_turn`: the turn at which cumulative output token savings exceed the protocol overhead

## Interpreting Results

### What success looks like

- Output token savings >90% on edit turns
- Input tokens flat across turns for GAP, growing for default
- Break-even at turn 1 or 2
- Envelope parse rate >80% (model can produce valid JSON)
- Apply success rate >70% (model produces correct search targets)

### What failure looks like

- Envelope parse rate <50% → model can't reliably produce the protocol format
- Apply success rate <50% → model hallucinates search targets
- No break-even within the conversation → protocol overhead never recovered
- GAP latency higher than default → structured output constraint slows generation

### What to investigate

- Which edit types produce the best savings (small value changes vs section rewrites)?
- Does model size affect envelope reliability? (4b vs 9b vs larger)
- How does artifact size affect the savings curve?
- Does the GAP system prompt need optimization, or is naive prompting sufficient?

## Running

```bash
# Single experiment
just bench-single n=1

# All experiments (requires Ollama running)
just bench

# With a different model
just bench model=qwen3.5:9b

# Results in benches/data/experiments/
```
