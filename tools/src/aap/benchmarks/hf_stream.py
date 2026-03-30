#!/usr/bin/env python3
"""
Streams a large pre-built HTML dashboard via a tokenizer, token by token.

Supports HuggingFace tokenizers (gpt2, bert-base-uncased, google/gemma-3-1b-it)
and tiktoken encodings (o200k_base, cl100k_base).

Usage: uv run --project python ag-hf-stream [output-path] [tokenizer]
"""
import sys
import time

from aap import make_tokenizer
from aap.assets import load_dashboard


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/artifact.html"
    tok_name = sys.argv[2] if len(sys.argv) > 2 else "gpt2"

    print(f"Tokenizer : {tok_name}")
    print(f"Output    : {path}")
    print("Loading tokenizer...", end=" ", flush=True)

    try:
        encode, decode = make_tokenizer(tok_name)
    except Exception as e:
        print(f"FAILED ({e})")
        sys.exit(1)

    print("done")

    html = load_dashboard()
    ids = encode(html)
    tokens = [decode([id]) for id in ids]

    total_tokens = len(tokens)
    total_bytes = len(html.encode())
    avg_chars = len(html) / total_tokens if total_tokens else 0

    print(f"Corpus    : {total_bytes:,} bytes  |  {total_tokens:,} tokens  |  avg {avg_chars:.1f} chars/token")
    print("Streaming...", end=" ", flush=True)

    flushes = 0
    t0 = time.perf_counter()

    with open(path, "w") as f:
        for token in tokens:
            f.write(token)
            f.flush()
            flushes += 1
            if flushes % 1000 == 0:
                print(".", end="", flush=True)

    elapsed = time.perf_counter() - t0
    kb = total_bytes / 1024
    kbps = kb / elapsed if elapsed > 0 else 0
    toks_sec = total_tokens / elapsed if elapsed > 0 else 0

    print(f"\n\n{'-'*44}")
    print(f"  Tokenizer     : {tok_name}")
    print(f"  Bytes written : {total_bytes:>10,}")
    print(f"  Tokens        : {total_tokens:>10,}")
    print(f"  Avg chars/tok : {avg_chars:>10.1f}")
    print(f"  Elapsed       : {elapsed:>10.2f} s")
    print(f"  Throughput    : {kbps:>10.1f} KB/s")
    print(f"  Tokens/sec    : {toks_sec:>10.0f}")
    print(f"  Flushes       : {flushes:>10,}")
    print(f"{'-'*44}")


if __name__ == "__main__":
    main()
