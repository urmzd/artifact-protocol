#!/usr/bin/env python3
"""
Sanity / perf test — streams a large pre-built HTML dashboard to the watched
file without any external dependencies.

Usage: uv run --project python ag-demo [output-path]
"""
import sys
import time

from aap.assets import load_dashboard
from aap.corpus import CHUNK_SIZE


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/artifact.html"

    html = load_dashboard()
    total = len(html)
    flushes = 0
    t0 = time.perf_counter()

    print(f"Streaming {total:,} bytes to {path}  (chunk={CHUNK_SIZE} chars, no delay)")

    with open(path, "w") as f:
        for i in range(0, total, CHUNK_SIZE):
            f.write(html[i : i + CHUNK_SIZE])
            f.flush()
            flushes += 1

    elapsed = time.perf_counter() - t0
    kb = total / 1024
    kbps = kb / elapsed if elapsed > 0 else 0

    print(f"\n{'-'*44}")
    print(f"  Bytes written : {total:>10,}")
    print(f"  Elapsed       : {elapsed:>10.2f} s")
    print(f"  Throughput    : {kbps:>10.1f} KB/s")
    print(f"  Flushes       : {flushes:>10,}")
    print(f"{'-'*44}")


if __name__ == "__main__":
    main()
