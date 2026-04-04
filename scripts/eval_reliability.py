"""Analyze GAP envelope reliability across experiments.

Reads metrics.json files and computes:
- Envelope parse success rate
- Apply engine success rate
- Failure modes (parse errors vs apply errors)
- Breakdown by format and edit type

Usage:
    python3 scripts/eval_reliability.py benches/data/experiments/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("usage: eval_reliability.py <experiments_dir>", file=sys.stderr)
        sys.exit(1)

    experiments_dir = Path(sys.argv[1])
    metrics_files = sorted(experiments_dir.glob("*/outputs/metrics.json"))

    if not metrics_files:
        print("No metrics.json files found. Run experiments first.", file=sys.stderr)
        sys.exit(1)

    # TODO: aggregate envelope reliability stats
    print(f"Found {len(metrics_files)} experiment results")


if __name__ == "__main__":
    main()
