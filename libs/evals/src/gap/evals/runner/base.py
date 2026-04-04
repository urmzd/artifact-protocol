"""Base flow runner — growing conversation, full regeneration each turn."""

from __future__ import annotations

import time
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models import Model

from ..agents import clean_artifact, collect_text_streaming_latency
from ..models import BaseTurnResult


async def run_base_turn0(
    llm: Model,
    system_prompt: str,
    turn0_prompt: str,
    output_dir: Path,
    ext: str,
) -> tuple[str, list, dict]:
    """Run turn-0 for the base flow.

    Returns (artifact_text, message_history, metrics_dict).
    """
    agent: Agent[None, str] = Agent(llm, system_prompt=system_prompt)
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
        return artifact, r.all_messages(), metrics


async def run_base_flow(
    llm: Model,
    system_prompt: str,
    history: list,
    edit_prompts: list[tuple[str, str]],
    output_dir: Path,
    ext: str,
) -> tuple[list[BaseTurnResult], str]:
    """Run all edit turns for the base flow.

    Returns (per_turn_results, final_artifact).
    """
    agent: Agent[None, str] = Agent(llm, system_prompt=system_prompt)
    results: list[BaseTurnResult] = []
    artifact = ""

    for turn_name, edit_prompt in edit_prompts:
        turn_num = int(turn_name.split("-")[1])
        t0 = time.perf_counter()

        try:
            async with agent.run_stream(edit_prompt, message_history=history) as r:
                raw_text, latency = await collect_text_streaming_latency(r)
                ms = int((time.perf_counter() - t0) * 1000)
                usage = r.usage()
                history = r.all_messages()
                artifact = clean_artifact(raw_text)
                (output_dir / f"{turn_name}{ext}").write_text(artifact)

                results.append(BaseTurnResult(
                    turn=turn_num,
                    edit=edit_prompt[:80],
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    latency_ms=ms,
                    output_bytes=len(artifact.encode()),
                    ttft_ms=latency.ttft_ms,
                    ttlt_ms=latency.ttlt_ms,
                    median_itl_ms=latency.median_itl_ms,
                ))
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            results.append(BaseTurnResult(
                turn=turn_num,
                edit=edit_prompt[:80],
                latency_ms=ms,
                failed=True,
                failure_reason=str(e),
            ))

    return results, artifact
