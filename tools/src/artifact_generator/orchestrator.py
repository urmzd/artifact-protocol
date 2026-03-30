"""
Parallel section orchestrator for aap/1.0 manifest mode.

Parses a manifest, dispatches section generations concurrently
(respecting dependency ordering), collects results, and assembles
the final artifact by stitching sections into the skeleton.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Callable, Awaitable

from artifact_generator.aap import (
    Envelope,
    SectionDef,
    SectionPrompt,
    new_id,
    now_iso,
    sha256_checksum,
)


# Type alias: a generator function takes (section_id, prompt, token_budget)
# and returns the generated content string.
SectionGenerator = Callable[[str, str, int | None], Awaitable[str]]


def parse_manifest(envelope: Envelope) -> tuple[str, list[SectionPrompt]]:
    """Extract skeleton and section prompts from a manifest envelope."""
    if envelope.mode != "manifest":
        raise ValueError(f"Expected manifest mode, got {envelope.mode}")
    if not envelope.skeleton:
        raise ValueError("Manifest missing skeleton")
    if not envelope.section_prompts:
        raise ValueError("Manifest missing section_prompts")
    return envelope.skeleton, envelope.section_prompts


def build_dependency_order(prompts: list[SectionPrompt]) -> list[list[str]]:
    """Compute execution waves from dependency graph.

    Returns a list of waves — each wave is a list of section IDs that
    can run in parallel. Waves execute sequentially.

    Example: if orders depends on stats, and nav/users have no deps:
      Wave 0: [nav, stats, users]  (parallel)
      Wave 1: [orders]             (after stats completes)
    """
    all_ids = {p.id for p in prompts}
    dep_map: dict[str, set[str]] = {}
    for p in prompts:
        dep_map[p.id] = set(p.dependencies) & all_ids

    resolved: set[str] = set()
    waves: list[list[str]] = []

    while resolved != all_ids:
        wave = [
            sid for sid in all_ids - resolved
            if dep_map[sid] <= resolved
        ]
        if not wave:
            unresolved = all_ids - resolved
            raise ValueError(f"Circular dependency detected among: {unresolved}")
        waves.append(sorted(wave))  # Sort for deterministic ordering
        resolved.update(wave)

    return waves


def assemble(skeleton: str, section_results: dict[str, str]) -> str:
    """Stitch section content into skeleton at marker positions.

    Each section marker pair:
        <!-- section:id --><!-- /section:id -->
    is replaced with:
        <!-- section:id -->
        <content>
        <!-- /section:id -->
    """
    result = skeleton
    for section_id, content in section_results.items():
        start_marker = f"<!-- section:{section_id} -->"
        end_marker = f"<!-- /section:{section_id} -->"
        si = result.find(start_marker)
        ei = result.find(end_marker)
        if si == -1 or ei == -1:
            raise ValueError(f"Section markers not found in skeleton: {section_id}")
        before = result[: si + len(start_marker)]
        after = result[ei:]
        result = f"{before}\n{content}\n{after}"
    return result


def assemble_update(
    base_content: str,
    section_results: dict[str, str],
) -> str:
    """Merge section results into existing artifact, preserving unchanged sections."""
    result = base_content
    for section_id, content in section_results.items():
        start_marker = f"<!-- section:{section_id} -->"
        end_marker = f"<!-- /section:{section_id} -->"
        si = result.find(start_marker)
        ei = result.find(end_marker)
        if si == -1 or ei == -1:
            raise ValueError(f"Section markers not found: {section_id}")
        before = result[: si + len(start_marker)]
        after = result[ei:]
        result = f"{before}\n{content}\n{after}"
    return result


async def orchestrate(
    manifest: Envelope,
    generator: SectionGenerator,
    base_content: str | None = None,
) -> tuple[Envelope, dict[str, str]]:
    """Execute a manifest: dispatch sections in parallel, assemble result.

    Args:
        manifest: A manifest-mode envelope.
        generator: Async function that generates content for a section.
            Signature: (section_id, prompt, token_budget) -> content_str
        base_content: For updates (manifest with base_version), the current
            artifact content. Unchanged sections are preserved.

    Returns:
        (result_envelope, section_results) — the assembled full envelope
        and a dict of section_id -> generated content.
    """
    skeleton, prompts = parse_manifest(manifest)
    prompt_map = {p.id: p for p in prompts}
    waves = build_dependency_order(prompts)

    section_results: dict[str, str] = {}
    section_tokens: dict[str, int] = {}

    for wave in waves:
        # Launch all sections in this wave concurrently
        async def gen_section(sp: SectionPrompt) -> tuple[str, str]:
            content = await generator(sp.id, sp.prompt, sp.token_budget)
            return sp.id, content

        tasks = [gen_section(prompt_map[sid]) for sid in wave]
        results = await asyncio.gather(*tasks)

        for sid, content in results:
            section_results[sid] = content

    # Assemble
    if base_content and manifest.base_version is not None:
        # Update mode: merge into existing
        final_content = assemble_update(base_content, section_results)
    else:
        # Initial generation: stitch into skeleton
        final_content = assemble(skeleton, section_results)

    # Build section definitions from the prompts
    section_defs = [
        SectionDef(
            id=sp.id,
            start_marker=f"<!-- section:{sp.id} -->",
            end_marker=f"<!-- /section:{sp.id} -->",
        )
        for sp in prompts
    ]

    result_envelope = Envelope(
        id=manifest.id,
        version=manifest.version,
        format=manifest.format,
        mode="full",
        content=final_content,
        created_at=now_iso() if manifest.base_version is None else None,
        updated_at=now_iso(),
        checksum=sha256_checksum(final_content),
        sections=section_defs,
    )

    return result_envelope, section_results


def orchestrate_sync(
    manifest: Envelope,
    generator_sync: Callable[[str, str, int | None], str],
    base_content: str | None = None,
) -> tuple[Envelope, dict[str, str]]:
    """Synchronous wrapper around orchestrate() for non-async contexts.

    The sync generator is wrapped in an async adapter internally.
    Sections within each wave still run concurrently via asyncio.
    """
    async def async_gen(sid: str, prompt: str, budget: int | None) -> str:
        # Run sync generator in thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, generator_sync, sid, prompt, budget)

    return asyncio.run(orchestrate(manifest, async_gen, base_content))
