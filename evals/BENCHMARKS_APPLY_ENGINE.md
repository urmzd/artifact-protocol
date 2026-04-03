# Apply Engine Benchmarks

Rust apply engine performance measured with [Criterion.rs](https://github.com/bheisler/criterion.rs) against real HTML dashboard fixtures (9-11 KB artifacts). Run with `cargo bench --bench aap` from the repo root.

## Test Environment

| Component | Value |
|---|---|
| CPU | Apple M4 Pro (12 cores) |
| RAM | 24 GB |
| Architecture | arm64 |
| OS | macOS 26.3.1 (Darwin) |
| Rust | 1.94.1 (2026-03-25) |
| Profile | `release` (optimized) |

## Payload Size Comparison

Envelope payload size as a percentage of the full artifact, measured across 4 fixture cases:

### Case 0001 (9,030 B artifact)

| Operation | Payload | % of Full |
|---|---:|---:|
| diff-replace (1 value) | 37 B | 0.4% |
| diff-replace (CSS value) | 49 B | 0.5% |
| diff-replace (longer) | 76 B | 0.8% |
| diff-replace (block) | 201 B | 2.2% |
| diff-multi (batch) | 161 B | 1.8% |
| section-single (small) | 116 B | 1.3% |
| section-single (medium) | 644 B | 7.1% |
| section-single (large) | 1,462 B | 16.2% |
| section-multi | 303 B | 3.4% |
| template-fill | 57 B | 0.6% |

### Case 0002 (9,269 B artifact)

| Operation | Payload | % of Full |
|---|---:|---:|
| diff-replace (1 value) | 37 B | 0.4% |
| diff-replace (CSS value) | 145 B | 1.6% |
| diff-replace (longer) | 57 B | 0.6% |
| diff-replace (block) | 81 B | 0.9% |
| diff-multi (batch) | 167 B | 1.8% |
| section-single (small) | 166 B | 1.8% |
| section-single (medium) | 189 B | 2.0% |
| section-single (large) | 919 B | 9.9% |
| section-single (xlarge) | 2,147 B | 23.2% |
| section-multi | 303 B | 3.3% |
| template-fill | 54 B | 0.6% |

### Case 0003 (9,337 B artifact)

| Operation | Payload | % of Full |
|---|---:|---:|
| diff-replace (1 value) | 37 B | 0.4% |
| diff-replace (CSS value) | 95 B | 1.0% |
| diff-replace (longer) | 85 B | 0.9% |
| diff-replace (block) | 213 B | 2.3% |
| diff-multi (batch) | 211 B | 2.3% |
| section-single (small) | 168 B | 1.8% |
| section-single (medium) | 540 B | 5.8% |
| section-single (large) | 897 B | 9.6% |
| section-single (xlarge) | 2,028 B | 21.7% |
| section-multi | 306 B | 3.3% |
| template-fill | 61 B | 0.7% |

### Summary

| Operation type | Typical payload range | Typical savings |
|---|---|---|
| diff-replace (single) | 37-213 B | **97.7-99.6%** |
| diff-multi (batch) | 161-211 B | **97.7-98.2%** |
| section-single | 116-2,147 B | **76.8-98.7%** |
| section-multi | 303-306 B | **96.6-96.7%** |
| template-fill | 54-61 B | **99.3-99.4%** |

## Apply Engine Timing

Time to resolve an envelope against a stored artifact. All operations are sub-microsecond to low-microsecond — negligible compared to LLM inference time.

### Full copy (baseline — memcpy cost)

| Artifact size | Time |
|---|---|
| ~9 KB (1x) | 121-125 ns |
| ~18 KB (2x) | 143-264 ns |
| ~28 KB (3x) | 159-403 ns |
| ~37 KB (4x) | 182-866 ns |

### Diff replace (search + splice)

| Envelope | Artifact size | Time |
|---|---|---|
| env_0 (37 B, single value) | 9 KB | 347-349 ns |
| env_0 (37 B, single value) | 14-19 KB | 450-453 ns |
| env_1 (49-145 B) | 9 KB | 663-664 ns |
| env_1 (49-145 B) | 14-19 KB | 748-751 ns |
| env_2 (76-85 B) | 9 KB | 932-935 ns |
| env_2 (76-85 B) | 14-19 KB | 1.03 µs |
| env_3 (201-213 B) | 9-11 KB | 1.37-1.55 µs |
| env_3 (201-213 B) | 14-19 KB | 1.60-1.82 µs |

### Key takeaways

- **All apply operations complete in < 2 µs** — orders of magnitude faster than LLM inference (seconds to minutes)
- Diff-replace scales linearly with artifact size (searching for the target string)
- Full copy scales linearly with artifact size (memcpy)
- The apply engine adds **zero token cost** — it's deterministic CPU work, not inference
- At these timescales, the apply engine is never the bottleneck; LLM output generation dominates wall-clock time
