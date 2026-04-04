"""GAP flow runner — stateless dispatch, envelope-based edits."""

from __future__ import annotations

import time
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models import Model

from ..agents import (
    StreamingLatency,
    clean_artifact,
    collect_structured_streaming_latency,
    collect_text_streaming_latency,
)
from ..apply import apply_envelope
from ..models import GAPTurnResult
from ..schema import LLMEnvelope


async def run_gap_turn0(
    llm: Model,
    init_system: str,
    turn0_prompt: str,
    output_dir: Path,
    ext: str,
) -> tuple[str, dict]:
    """Run turn-0 for the GAP flow (with target markers).

    Returns (artifact_text, metrics_dict).
    """
    agent: Agent[None, str] = Agent(llm, system_prompt=init_system)
    t0 = time.perf_counter()
    async with agent.run_stream(turn0_prompt) as r:
        raw_text, latency = await collect_text_streaming_latency(r)
        ms = int((time.perf_counter() - t0) * 1000)
        usage = r.usage()
        artifact = clean_artifact(raw_text)
        (output_dir / f"turn-0{ext}").write_text(artifact)

        metrics = {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "latency_ms": ms,
            "artifact_bytes": len(artifact.encode()),
            "ttft_ms": latency.ttft_ms,
            "ttlt_ms": latency.ttlt_ms,
            "median_itl_ms": latency.median_itl_ms,
        }
        return artifact, metrics


async def run_gap_flow(
    llm: Model,
    maintain_system: str,
    artifact: str,
    edit_prompts: list[tuple[str, str]],
    fmt: str,
    output_dir: Path,
    ext: str,
) -> tuple[list[GAPTurnResult], str]:
    """Run all edit turns for the GAP flow.

    Returns (per_turn_results, final_artifact).
    """
    maintain_agent: Agent[None, LLMEnvelope] = Agent(
        llm,
        system_prompt=maintain_system,
        output_type=LLMEnvelope,
    )

    results: list[GAPTurnResult] = []
    version = 1

    for turn_name, edit_prompt in edit_prompts:
        turn_num = int(turn_name.split("-")[1])
        user_msg = (
            f"## Current Artifact\n\n```\n{artifact}\n```\n\n"
            f"## Edit Instruction\n\n{edit_prompt}"
        )

        t0 = time.perf_counter()
        parsed = False
        succeeded = False
        env_name = ""
        envelope_json = ""
        latency = StreamingLatency()
        usage = type("U", (), {"input_tokens": 0, "output_tokens": 0})()

        try:
            async with maintain_agent.run_stream(user_msg) as r:
                envelope, latency = await collect_structured_streaming_latency(r)
                ms = int((time.perf_counter() - t0) * 1000)
                usage = r.usage()

                parsed = True
                env_name = envelope.name
                envelope_json = envelope.model_dump_json(indent=2)

                new_artifact = apply_envelope(artifact, envelope, fmt)
                succeeded = True
                artifact = new_artifact
                version += 1

        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)

        if envelope_json:
            (output_dir / f"{turn_name}.json").write_text(envelope_json)
        (output_dir / f"{turn_name}{ext}").write_text(artifact)

        results.append(GAPTurnResult(
            turn=turn_num,
            edit=edit_prompt[:80],
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=ms,
            output_bytes=len(artifact.encode()),
            ttft_ms=latency.ttft_ms,
            ttlt_ms=latency.ttlt_ms,
            median_itl_ms=latency.median_itl_ms,
            envelope_parsed=parsed,
            apply_succeeded=succeeded,
            envelope_name=env_name,
            failed=not succeeded,
            failure_reason="" if succeeded else "parse or apply failed",
        ))

    return results, artifact
