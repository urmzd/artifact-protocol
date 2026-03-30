#!/usr/bin/env python3
"""
Parallel generation demo — manifest-driven concurrent section generation.

Demonstrates how a manifest splits artifact generation into independent
sections, dispatches them in parallel, and assembles the result.
Then shows how a follow-up update only regenerates changed sections.

Usage: uv run --project tools ag-parallel-demo
"""
import asyncio
import json
import time

from artifact_generator.aap import (
    Envelope,
    SectionPrompt,
    SectionDef,
    now_iso,
    sha256_checksum,
)
from artifact_generator.orchestrator import (
    orchestrate,
    build_dependency_order,
    assemble,
    assemble_update,
)


# ── Simulated section generators ─────────────────────────────────────────────
# In a real system these would be LLM calls (tool_use / agent spawns).
# We simulate latency and token costs.

SECTION_CONTENT = {
    "nav": """\
<aside>
  <div class="sidebar-section">Main</div>
  <a class="sidebar-link active" href="#">Dashboard</a>
  <a class="sidebar-link" href="#">Analytics</a>
  <a class="sidebar-link" href="#">Reports</a>
  <div class="sidebar-section">Management</div>
  <a class="sidebar-link" href="#">Users</a>
  <a class="sidebar-link" href="#">Orders</a>
</aside>""",
    "stats": """\
<div class="stats">
  <div class="card"><span class="label">Users</span><span class="value">24,891</span></div>
  <div class="card"><span class="label">Revenue</span><span class="value">$182,430</span></div>
  <div class="card"><span class="label">Orders</span><span class="value">3,047</span></div>
  <div class="card"><span class="label">Uptime</span><span class="value">99.97%</span></div>
</div>""",
    "users": """\
<table>
  <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Alice Smith</td><td>alice@example.com</td><td>Admin</td></tr>
    <tr><td>2</td><td>Bob Johnson</td><td>bob@example.com</td><td>User</td></tr>
    <tr><td>3</td><td>Carol Williams</td><td>carol@example.com</td><td>Editor</td></tr>
  </tbody>
</table>""",
    "orders": """\
<table>
  <thead><tr><th>ID</th><th>Product</th><th>Amount</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>ORD-001</td><td>Widget Pro</td><td>$29.99</td><td>Shipped</td></tr>
    <tr><td>ORD-002</td><td>Gadget Plus</td><td>$149.00</td><td>Processing</td></tr>
    <tr><td>ORD-003</td><td>Doohickey Max</td><td>$89.50</td><td>Delivered</td></tr>
  </tbody>
</table>""",
}

# Updated content for the v2 update
UPDATED_STATS = """\
<div class="stats">
  <div class="card"><span class="label">Users</span><span class="value">31,205</span></div>
  <div class="card"><span class="label">Revenue</span><span class="value">$210,880</span></div>
  <div class="card"><span class="label">Orders</span><span class="value">4,112</span></div>
  <div class="card"><span class="label">Uptime</span><span class="value">99.99%</span></div>
</div>"""

# Simulated per-section generation latency (seconds)
LATENCIES = {"nav": 0.3, "stats": 0.5, "users": 0.8, "orders": 0.4}


async def mock_generator(section_id: str, prompt: str, budget: int | None) -> str:
    """Simulate an LLM generating a section with realistic latency."""
    latency = LATENCIES.get(section_id, 0.5)
    await asyncio.sleep(latency)
    return SECTION_CONTENT[section_id]


async def mock_generator_v2(section_id: str, prompt: str, budget: int | None) -> str:
    """Simulate generating only updated sections."""
    await asyncio.sleep(0.3)
    if section_id == "stats":
        return UPDATED_STATS
    return SECTION_CONTENT[section_id]


async def run():
    print("=" * 70)
    print("  Agent-Artifact Protocol (AAP) — Parallel Generation Demo")
    print("=" * 70)

    # ── Step 1: Build manifest ────────────────────────────────────────────
    skeleton = """\
<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>body{font-family:system-ui;margin:0} .layout{display:flex}</style>
</head><body>
<div class="layout">
<!-- section:nav --><!-- /section:nav -->
<main>
<!-- section:stats --><!-- /section:stats -->
<!-- section:users --><!-- /section:users -->
<!-- section:orders --><!-- /section:orders -->
</main>
</div>
</body></html>"""

    manifest = Envelope(
        id="parallel-demo",
        version=1,
        format="text/html",
        mode="manifest",
        skeleton=skeleton,
        section_prompts=[
            SectionPrompt(id="nav", prompt="Generate sidebar navigation"),
            SectionPrompt(id="stats", prompt="Generate 4 stat cards"),
            SectionPrompt(id="users", prompt="Generate users table with 3 rows"),
            SectionPrompt(id="orders", prompt="Generate orders table", dependencies=["stats"]),
        ],
    )

    print(f"\nManifest: {len(manifest.section_prompts)} sections")
    waves = build_dependency_order(manifest.section_prompts)
    for i, wave in enumerate(waves):
        print(f"  Wave {i}: {wave} (parallel)")

    # ── Step 2: Execute in parallel ───────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("  Step 1: Parallel initial generation")
    print(f"{'─' * 70}")

    # Sequential timing (for comparison)
    seq_time = sum(LATENCIES.values())
    print(f"  Sequential estimate: {seq_time:.1f}s (sum of all section latencies)")

    t0 = time.perf_counter()
    result_envelope, section_results = await orchestrate(manifest, mock_generator)
    parallel_time = time.perf_counter() - t0

    print(f"  Parallel actual:    {parallel_time:.2f}s")
    print(f"  Speedup:            {seq_time / parallel_time:.1f}x")
    print()
    for sid, content in section_results.items():
        print(f"  {sid:>10}: {len(content):>4} chars")
    print(f"  {'TOTAL':>10}: {len(result_envelope.content):>4} chars assembled")

    # ── Step 3: Parallel update — only changed sections ───────────────────
    print(f"\n{'─' * 70}")
    print("  Step 2: Parallel update (only stats section changed)")
    print(f"{'─' * 70}")

    update_manifest = Envelope(
        id="parallel-demo",
        version=2,
        format="text/html",
        mode="manifest",
        base_version=1,
        skeleton=skeleton,
        section_prompts=[
            SectionPrompt(id="stats", prompt="Update stat cards with Q2 data"),
        ],
    )

    t1 = time.perf_counter()
    updated_envelope, update_results = await orchestrate(
        update_manifest, mock_generator_v2, base_content=result_envelope.content
    )
    update_time = time.perf_counter() - t1

    print(f"  Sections regenerated: {list(update_results.keys())}")
    print(f"  Update time:          {update_time:.2f}s")
    print(f"  v1 total chars:       {len(result_envelope.content):,}")
    print(f"  v2 total chars:       {len(updated_envelope.content):,}")
    print(f"  Update payload:       {sum(len(c) for c in update_results.values()):,} chars (only changed sections)")

    # Verify unchanged sections are preserved
    v1 = result_envelope.content
    v2 = updated_envelope.content
    assert "alice@example.com" in v2, "Users section should be preserved"
    assert "31,205" in v2, "Stats should be updated"
    assert "24,891" not in v2, "Old stats should be gone"

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("  Summary")
    print(f"{'=' * 70}")
    print(f"  Initial generation:")
    print(f"    Sequential: {seq_time:.1f}s wall-clock")
    print(f"    Parallel:   {parallel_time:.2f}s wall-clock ({seq_time / parallel_time:.1f}x faster)")
    print(f"  Update (1 of {len(SECTION_CONTENT)} sections):")
    print(f"    Full regen: {seq_time:.1f}s + all tokens")
    print(f"    Parallel:   {update_time:.2f}s + {sum(len(c) for c in update_results.values())} chars")
    full_chars = len(result_envelope.content)
    update_chars = sum(len(c) for c in update_results.values())
    print(f"    Token savings: {(1 - update_chars / full_chars) * 100:.1f}%")
    print()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
