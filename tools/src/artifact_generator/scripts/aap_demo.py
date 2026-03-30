#!/usr/bin/env python3
"""
Agent-Artifact Protocol (AAP) lifecycle demo — walks through create, diff, section, template.

Demonstrates the full protocol lifecycle with the dashboard corpus,
showing how each mode reduces token cost for different edit patterns.

Usage: uv run --project tools ag-aap-demo
"""
import json

from artifact_generator.assets import load_dashboard
from artifact_generator.aap import (
    Envelope,
    SectionDef,
    apply_diff,
    apply_section_update,
    fill_template,
    sha256_checksum,
)
from artifact_generator.strategies import (
    generate_full,
    generate_diff,
    generate_section_update,
    generate_template_fill,
)


def print_envelope(label: str, env: Envelope):
    d = env.to_dict()
    # Truncate content for display
    if "content" in d and d["content"] and len(d["content"]) > 200:
        d["content"] = d["content"][:200] + f"... ({len(env.content):,} chars total)"
    if "template" in d and d["template"] and len(d["template"]) > 200:
        d["template"] = d["template"][:200] + f"... ({len(env.template):,} chars total)"
    print(f"\n{'─' * 70}")
    print(f"  {label}")
    print(f"{'─' * 70}")
    print(json.dumps(d, indent=2))


def main():
    print("=" * 70)
    print("  Agent-Artifact Protocol (AAP) — Lifecycle Demo")
    print("=" * 70)

    html = load_dashboard()
    print(f"\nLoaded dashboard: {len(html):,} chars")

    # ── Step 1: Full generation ───────────────────────────────────────────────
    # Add section markers for the demo
    sectioned = html.replace(
        '<div class="stats">',
        '<!-- section:stats -->\n<div class="stats">',
    )
    # Find the closing point for stats section
    stats_end = sectioned.find('</div>\n    </div>\n    <div class="section">\n      <div class="section-header">\n        <span class="section-title">Users</span>')
    if stats_end != -1:
        sectioned = (
            sectioned[:stats_end]
            + '</div>\n    </div>\n<!-- /section:stats -->\n    <div class="section">\n      <div class="section-header">\n        <span class="section-title">Users</span>'
            + sectioned[stats_end + len('</div>\n    </div>\n    <div class="section">\n      <div class="section-header">\n        <span class="section-title">Users</span>'):]
        )

    sections = [
        SectionDef(id="stats", start_marker="<!-- section:stats -->", end_marker="<!-- /section:stats -->"),
    ]

    env1 = generate_full(sectioned, artifact_id="demo-dashboard", sections=sections)
    print_envelope("Step 1: Full Generation (v1)", env1)
    store = {env1.id: sectioned}

    # ── Step 2: Diff update — change one stat value ───────────────────────────
    new_html = sectioned.replace(
        '<div class="card-value">24,891</div>',
        '<div class="card-value">27,103</div>',
    )

    env2 = generate_diff("demo-dashboard", 1, sectioned, new_html, version=2)
    env2.tokens_used = sum(
        len(op.content or "") + len(op.target.search or "")
        for op in env2.operations
    )
    print_envelope("Step 2: Diff Update (v2) — change 1 stat value", env2)

    resolved = apply_diff(store["demo-dashboard"], env2.operations)
    assert resolved == new_html, "Diff verification failed!"
    store["demo-dashboard"] = resolved
    print(f"\n  Verified: diff applied correctly ({len(env2.operations)} operation(s))")

    # ── Step 3: Section update — replace stats section ────────────────────────
    new_stats = """<div class="stats">
      <div class="card"><div class="card-label">Total Users</div>
        <div class="card-value">31,205</div>
        <div class="card-delta up">&#9650; 8.1%</div></div>
      <div class="card"><div class="card-label">Revenue</div>
        <div class="card-value">$210,880</div>
        <div class="card-delta up">&#9650; 15.6%</div></div>
      <div class="card"><div class="card-label">Orders</div>
        <div class="card-value">4,112</div>
        <div class="card-delta up">&#9650; 6.3%</div></div>
      <div class="card"><div class="card-label">Uptime</div>
        <div class="card-value">99.99%</div>
        <div class="card-delta up">SLA: 99.9%</div></div>
    </div>"""

    env3 = generate_section_update("demo-dashboard", 2, {"stats": new_stats}, version=3)
    print_envelope("Step 3: Section Update (v3) — replace stats", env3)

    resolved = apply_section_update(store["demo-dashboard"], env3.target_sections)
    store["demo-dashboard"] = resolved
    print(f"\n  Verified: section update applied ({len(env3.target_sections)} section(s))")

    # ── Step 4: Template fill — same layout, different data ───────────────────
    template = """<!DOCTYPE html>
<html><head><title>{{title}}</title></head>
<body>
<h1>{{title}}</h1>
<div class="stats">
  <div class="stat">Users: {{users}}</div>
  <div class="stat">Revenue: {{revenue}}</div>
</div>
<div class="content">{{{body_html}}}</div>
</body></html>"""

    bindings = {
        "title": "Q2 2026 Summary",
        "users": "35,400",
        "revenue": "$248,000",
        "body_html": "<p>Strong growth across all segments.</p><table><tr><td>Enterprise</td><td>+22%</td></tr></table>",
    }

    env4 = generate_template_fill(template, bindings, artifact_id="demo-summary", version=1)
    print_envelope("Step 4: Template Fill (v1) — new artifact from template", env4)

    resolved = fill_template(template, bindings)
    print(f"\n  Resolved template ({len(resolved):,} chars)")
    print(f"  Checksum: {sha256_checksum(resolved)}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("  Summary")
    print(f"{'=' * 70}")
    print(f"  v1: full       — {len(sectioned):>6,} chars (baseline)")
    print(f"  v2: diff       — {sum(len(op.content or '') + len(op.target.search or '') for op in env2.operations):>6,} chars (search + replace payload)")
    print(f"  v3: section    — {sum(len(s.content) for s in env3.target_sections):>6,} chars (section content)")
    print(f"  v4: template   — {sum(len(v) for v in bindings.values()):>6,} chars (bindings only)")
    print()


if __name__ == "__main__":
    main()
