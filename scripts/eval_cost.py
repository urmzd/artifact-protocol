"""Analyze token costs across experiment results.

Reads metrics.json files from experiment output directories and computes:
- Per-turn input/output token comparison (base vs GAP)
- Cumulative cost curves
- Break-even turn identification
- Protocol overhead amortization

Usage:
    python3 scripts/eval_cost.py benches/data/experiments/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_metrics(experiments_dir: Path) -> list[dict]:
    results = []
    for metrics_file in sorted(experiments_dir.glob("*/outputs/metrics.json")):
        results.append(json.loads(metrics_file.read_text()))
    return results


def main():
    if len(sys.argv) < 2:
        print("usage: eval_cost.py <experiments_dir>", file=sys.stderr)
        sys.exit(1)

    experiments_dir = Path(sys.argv[1])
    results = load_metrics(experiments_dir)

    if not results:
        print("No metrics.json files found. Run experiments first.", file=sys.stderr)
        sys.exit(1)

    # TODO: aggregate and display results
    print(f"Loaded {len(results)} experiment results")


if __name__ == "__main__":
    main()
