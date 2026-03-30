#!/usr/bin/env python3
"""
Token savings benchmark — measures token cost of each AAP generation mode.

Compares full regeneration vs diff, section update, and template fill
across realistic edit scenarios using the dashboard corpus.

Usage: uv run --project tools ag-aap-bench
"""
import re

from artifact_generator import make_tokenizer
from artifact_generator.assets import load_dashboard
from artifact_generator.aap import Envelope, apply_diff, apply_section_update, fill_template
from artifact_generator.strategies import (
    generate_full,
    generate_diff,
    generate_section_update,
    generate_template_fill,
    extract_sections,
)

TOKENIZER = "o200k_base"  # GPT-4 tokenizer for consistent measurement


def count_tokens(text: str, encode) -> int:
    return len(encode(text))


def count_envelope_tokens(envelope: Envelope, encode) -> int:
    """Count tokens in the envelope payload (content fields only, not metadata)."""
    total = 0
    if envelope.content:
        total += count_tokens(envelope.content, encode)
    for op in envelope.operations:
        if op.target.search:
            total += count_tokens(op.target.search, encode)
        if op.content:
            total += count_tokens(op.content, encode)
    for s in envelope.target_sections:
        total += count_tokens(s.content, encode)
    if envelope.template:
        total += count_tokens(envelope.template, encode)
    if envelope.bindings:
        for v in envelope.bindings.values():
            if isinstance(v, str):
                total += count_tokens(v, encode)
    return total


# ── edit scenarios ────────────────────────────────────────────────────────────


def edit_single_value(html: str) -> str:
    """Change one stat card value."""
    return html.replace(
        '<div class="card-value">24,891</div>',
        '<div class="card-value">27,103</div>',
    )


def edit_add_table_rows(html: str) -> str:
    """Add 5 rows to the users table."""
    new_rows = ""
    for i in range(5):
        new_rows += (
            f'<tr><td>{151+i}</td><td>New User {i+1}</td>'
            f'<td>new{i+1}@example.com</td><td>Viewer</td>'
            f'<td><span style="background:#22c55e;color:#fff;padding:2px 8px;'
            f'border-radius:12px;font-size:12px">Active</span></td>'
            f'<td>2026-03-29</td></tr>'
        )
    return html.replace("</tbody>\n      </table></div>\n    </div>\n    <div class=\"section\">\n      <div class=\"section-header\">\n        <span class=\"section-title\">Recent Orders</span>",
                         new_rows + "</tbody>\n      </table></div>\n    </div>\n    <div class=\"section\">\n      <div class=\"section-header\">\n        <span class=\"section-title\">Recent Orders</span>")


def edit_css_colors(html: str) -> str:
    """Change the primary blue color throughout CSS."""
    return html.replace("#2563eb", "#7c3aed").replace("#3b82f6", "#8b5cf6").replace("#1d4ed8", "#6d28d9")


def build_template_and_bindings(html: str) -> tuple[str, dict[str, str]]:
    """Extract a template from the dashboard with data slots."""
    template = html
    bindings = {}

    # Replace stat values with slots
    stats = [
        ("24,891", "total_users"),
        ("$182,430", "revenue"),
        ("3,047", "orders"),
        ("99.97%", "uptime"),
    ]
    for value, slot in stats:
        template = template.replace(value, f"{{{{{slot}}}}}", 1)
        bindings[slot] = value

    return template, bindings


def template_new_data(template: str) -> dict[str, str]:
    """New bindings for the same template."""
    return {
        "total_users": "31,205",
        "revenue": "$210,880",
        "orders": "4,112",
        "uptime": "99.99%",
    }


# ── benchmark runner ────────────────────────────────────────────────────────


def main():
    print(f"Loading tokenizer: {TOKENIZER}...", end=" ", flush=True)
    encode, _ = make_tokenizer(TOKENIZER)
    print("done")

    print("Loading dashboard HTML...", end=" ", flush=True)
    html = load_dashboard()
    print(f"done  ({len(html):,} chars)")
    print()

    full_tokens = count_tokens(html, encode)
    print(f"Baseline (full regeneration): {full_tokens:,} tokens")
    print()

    results = []

    # Scenario 1: Single value change
    new_html = edit_single_value(html)
    env = generate_diff("bench", 1, html, new_html, version=2)
    resolved = apply_diff(html, env.operations)
    assert resolved == new_html, "Diff apply failed"
    diff_tokens = count_envelope_tokens(env, encode)
    results.append(("Change 1 stat value", full_tokens, diff_tokens, "diff", None, None))

    # Scenario 2: Add table rows
    new_html = edit_add_table_rows(html)
    env = generate_diff("bench", 1, html, new_html, version=2)
    resolved = apply_diff(html, env.operations)
    assert resolved == new_html, "Diff apply failed for add rows"
    diff_tokens = count_envelope_tokens(env, encode)
    results.append(("Add 5 table rows", full_tokens, diff_tokens, "diff", None, None))

    # Scenario 3: CSS color changes
    new_html = edit_css_colors(html)
    env = generate_diff("bench", 1, html, new_html, version=2)
    diff_tokens = count_envelope_tokens(env, encode)
    results.append(("Update CSS colors", full_tokens, diff_tokens, "diff", None, None))

    # Scenario 4: Section update (replace users table header)
    # Add section markers to html for this test
    sectioned_html = html.replace(
        '<div class="stats">',
        '<!-- section:stats -->\n<div class="stats">',
    ).replace(
        '</div>\n    </div>\n    <div class="section">\n      <div class="section-header">\n        <span class="section-title">Users</span>',
        '</div>\n    </div>\n<!-- /section:stats -->\n    <div class="section">\n      <div class="section-header">\n        <span class="section-title">Users</span>',
    )
    new_stats = """<div class="stats">
      <div class="card"><div class="card-label">Total Users</div>
        <div class="card-value">31,205</div>
        <div class="card-delta up">&#9650; 8.1% vs last month</div></div>
      <div class="card"><div class="card-label">Revenue (MTD)</div>
        <div class="card-value">$210,880</div>
        <div class="card-delta up">&#9650; 15.6% vs last month</div></div>
      <div class="card"><div class="card-label">Orders (MTD)</div>
        <div class="card-value">4,112</div>
        <div class="card-delta up">&#9650; 6.3% vs last month</div></div>
      <div class="card"><div class="card-label">Uptime</div>
        <div class="card-value">99.99%</div>
        <div class="card-delta up">SLA: 99.9%</div></div>
    </div>"""
    env = generate_section_update("bench", 1, {"stats": new_stats}, version=2)
    section_tokens = count_envelope_tokens(env, encode)
    results.append(("Replace stats section", full_tokens, None, None, section_tokens, "section"))

    # Scenario 5: Template fill with new data
    template, original_bindings = build_template_and_bindings(html)
    template_tokens = count_tokens(template, encode)
    new_bindings = template_new_data(template)
    env = generate_template_fill(template, new_bindings, artifact_id="bench", version=2)
    binding_tokens = count_envelope_tokens(env, encode)
    # For reprovisioning, we only need to send bindings (template already registered)
    rebind_tokens = sum(count_tokens(v, encode) for v in new_bindings.values())
    results.append(("New data (template)", full_tokens, None, None, None, None))

    # ── results table ─────────────────────────────────────────────────────────
    print()
    print("=" * 95)
    print(f"{'Edit Scenario':<26} {'Full':>8} {'Mode':<10} {'Tokens':>8} {'Savings':>8} {'Reduction':>10}")
    print("=" * 95)

    for name, full, diff_t, diff_mode, sec_t, sec_mode in results:
        if diff_t is not None:
            pct = (1 - diff_t / full) * 100
            print(f"{name:<26} {full:>8,} {'diff':<10} {diff_t:>8,} {full - diff_t:>8,} {pct:>9.1f}%")
        if sec_t is not None:
            pct = (1 - sec_t / full) * 100
            print(f"{name:<26} {full:>8,} {'section':<10} {sec_t:>8,} {full - sec_t:>8,} {pct:>9.1f}%")

    # Template row
    print(f"{'New data (template)':<26} {full_tokens:>8,} {'template':<10} {rebind_tokens:>8,} {full_tokens - rebind_tokens:>8,} {(1 - rebind_tokens / full_tokens) * 100:>9.1f}%")
    print(f"{'First fill (template)':<26} {full_tokens:>8,} {'template':<10} {binding_tokens:>8,} {full_tokens - binding_tokens:>8,} {(1 - binding_tokens / full_tokens) * 100:>9.1f}%")

    print("=" * 95)
    print()
    print("Token counts use tiktoken o200k_base (GPT-4 tokenizer).")
    print("'Full' = tokens to regenerate entire artifact. 'Tokens' = tokens for the update payload.")
    print("Savings = absolute token reduction. Reduction = percentage decrease.")


if __name__ == "__main__":
    main()
