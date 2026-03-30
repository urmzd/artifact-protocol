#!/usr/bin/env python3
"""
Offline tokenizer benchmark — no server needed.

Compares HuggingFace tokenizers, tiktoken encodings, and fixed chunking across:
  - token count, avg chars/token, tokenize time, tokens/sec
  - simulated streaming throughput (file writes, no delay)

Usage: uv run --project python ag-bench
"""
import time
import tempfile
import os

from aap import make_tokenizer, HF_TOKENIZERS, TT_ENCODINGS
from aap.assets import load_dashboard
from aap.corpus import CHUNK_SIZE

N_REPS = 100


def bench_tokenizer(name: str, html: str) -> dict:
    print(f"  Loading {name}...", end=" ", flush=True)
    encode, decode = make_tokenizer(name)
    print("done")

    # Warm-up
    encode(html)

    # Time N_REPS encodes
    t0 = time.perf_counter()
    for _ in range(N_REPS):
        ids = encode(html)
    elapsed = time.perf_counter() - t0

    n_tok = len(ids)
    avg_ms = (elapsed / N_REPS) * 1000
    tps = n_tok / (elapsed / N_REPS)
    avg_ch = len(html) / n_tok if n_tok else 0

    # Simulate streaming (file writes, no delay)
    tokens = [decode([id]) for id in ids]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        tmp = f.name
        t1 = time.perf_counter()
        for token in tokens:
            f.write(token)
            f.flush()
        stream_elapsed = time.perf_counter() - t1
    os.unlink(tmp)

    kb = len(html.encode()) / 1024
    kbps = kb / stream_elapsed if stream_elapsed > 0 else 0

    return {
        "name": name,
        "n_tok": n_tok,
        "avg_ch": avg_ch,
        "tok_ms": avg_ms,
        "tps": tps,
        "stream_elapsed": stream_elapsed,
        "kbps": kbps,
        "flushes": n_tok,
    }


def bench_fixed(html: str) -> dict:
    chunk = CHUNK_SIZE
    n_chunks = len(range(0, len(html), chunk))

    # Time N_REPS chunking passes
    t0 = time.perf_counter()
    for _ in range(N_REPS):
        chunks = [html[i : i + chunk] for i in range(0, len(html), chunk)]
    elapsed = time.perf_counter() - t0

    avg_ms = (elapsed / N_REPS) * 1000
    tps = n_chunks / (elapsed / N_REPS)

    # Simulate streaming
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        tmp = f.name
        t1 = time.perf_counter()
        for ch in chunks:
            f.write(ch)
            f.flush()
        stream_elapsed = time.perf_counter() - t1
    os.unlink(tmp)

    kb = len(html.encode()) / 1024
    kbps = kb / stream_elapsed if stream_elapsed > 0 else 0

    return {
        "name": f"Fixed {chunk}-char chunks",
        "n_tok": n_chunks,
        "avg_ch": chunk,
        "tok_ms": avg_ms,
        "tps": tps,
        "stream_elapsed": stream_elapsed,
        "kbps": kbps,
        "flushes": n_chunks,
    }


def fmt_k(n: float) -> str:
    return f"{n/1000:.0f}k" if n >= 1000 else str(int(n))


def main():
    print("Loading dashboard HTML...", end=" ", flush=True)
    html = load_dashboard()
    print(f"done  ({len(html):,} chars / {len(html.encode()):,} bytes)")
    print()

    print(f"Benchmarking (tokenize x {N_REPS} reps each):")
    results = []
    for name in HF_TOKENIZERS + TT_ENCODINGS:
        try:
            results.append(bench_tokenizer(name, html))
        except Exception as e:
            print(f"  Loading {name}... SKIPPED ({e})")
    results.append(bench_fixed(html))

    # ── tokenization table ─────────────────────────────────────────────────────
    print()
    print("-" * 82)
    print(f"{'Tokenizer':<26} {'Tokens':>8} {'Avg ch/tok':>11} {'Tok ms':>9} {'Tokens/sec':>12}")
    print("-" * 82)
    for r in results:
        print(
            f"{r['name']:<26} {r['n_tok']:>8,} {r['avg_ch']:>11.1f}"
            f" {r['tok_ms']:>9.1f} {fmt_k(r['tps']):>12}"
        )
    print("-" * 82)

    # ── streaming simulation table ─────────────────────────────────────────────
    print()
    print("-" * 82)
    print(f"{'Tokenizer':<26} {'Flushes':>8} {'Elapsed s':>10} {'KB/s':>8}")
    print("-" * 82)
    for r in results:
        print(
            f"{r['name']:<26} {r['flushes']:>8,} {r['stream_elapsed']:>10.3f}"
            f" {r['kbps']:>8.1f}"
        )
    print("-" * 82)


if __name__ == "__main__":
    main()
