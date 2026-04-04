"""Artifact generation and LLM model factory."""

from __future__ import annotations

import os
import re
import statistics
import time
from dataclasses import dataclass, field

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.concurrency import ConcurrencyLimitedModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider


# ── Provider defaults ─────────────────────────────────────────────────────

PROVIDER_DEFAULTS: dict[str, str] = {
    "google": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "ollama": "gemma4",
    "github": "openai/gpt-4o-mini",
    "groq": "qwen3-32b",
}


# ── Model factory ───────────────────────────────────────────────────────────


def _build_model(provider: str, model_name: str, host: str) -> Model:
    if provider == "google":
        model: Model = GoogleModel(
            model_name=model_name or PROVIDER_DEFAULTS["google"],
            provider=GoogleProvider(),
        )
        # Gemini free tier: 15 RPM — serialize requests
        return ConcurrencyLimitedModel(model, limiter=1)
    elif provider == "openai":
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["openai"],
            provider=OpenAIProvider(),
        )
    elif provider == "github":
        from pydantic_ai.providers.github import GitHubProvider
        api_key = os.environ.get("GITHUB_TOKEN") or os.popen("gh auth token").read().strip()
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["github"],
            provider=GitHubProvider(api_key=api_key),
        )
    elif provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["groq"],
            provider=OpenAIProvider(
                base_url="https://api.groq.com/openai/v1",
                api_key=api_key,
            ),
        )
    elif provider == "ollama":
        api_key = os.environ.get("OLLAMA_API_KEY")
        if api_key:
            # Ollama Cloud: https://ollama.com/v1 (OpenAI-compatible)
            base = "https://ollama.com/v1"
        else:
            # Local Ollama
            base = host.rstrip("/")
            if not base.endswith("/v1"):
                base += "/v1"
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["ollama"],
            provider=OllamaProvider(base_url=base, api_key=api_key),
        )
    else:
        raise ValueError(f"unsupported provider: {provider}")


def create_model(
    provider: str,
    model_name: str,
    host: str,
    fallback: str = "",
) -> Model:
    primary = _build_model(provider, model_name, host)
    if not fallback:
        return primary
    fallback_models = [_build_model(fb.strip(), "", host) for fb in fallback.split(",")]
    return FallbackModel(primary, *fallback_models)


# ── Artifact generation (for corpus) ────────────────────────────────────────


def clean_artifact(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1 :]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text


async def generate_artifact(model: Model, prompt: str) -> str:
    """Generate a single artifact. Returns cleaned content."""
    agent: Agent[None, str] = Agent(
        model,
        system_prompt="You are a code generator. Output only raw code/content. No markdown fences, no explanation.",
    )
    result = await agent.run(prompt)
    return clean_artifact(result.output)


# ── Streaming latency helpers ────────────────────────────────────────────


@dataclass
class StreamingLatency:
    """Latency metrics collected from a streaming response."""

    ttft_ms: int | None = None
    ttlt_ms: int | None = None
    median_itl_ms: float | None = None


def _latency_from_timestamps(t0: float, timestamps: list[float]) -> StreamingLatency:
    """Compute TTFT, TTLT, and median ITL from a list of chunk arrival times."""
    if not timestamps:
        return StreamingLatency()
    ttft_ms = int((timestamps[0] - t0) * 1000)
    ttlt_ms = int((timestamps[-1] - t0) * 1000)
    median_itl_ms = None
    if len(timestamps) > 1:
        intervals = [
            (timestamps[i] - timestamps[i - 1]) * 1000
            for i in range(1, len(timestamps))
        ]
        median_itl_ms = round(statistics.median(intervals), 2)
    return StreamingLatency(ttft_ms=ttft_ms, ttlt_ms=ttlt_ms, median_itl_ms=median_itl_ms)


async def collect_text_streaming_latency(stream_result) -> tuple[str, StreamingLatency]:
    """Consume a text StreamedRunResult via stream_text and collect latency metrics.

    Use for agents with plain text output. Returns (full_text, StreamingLatency).
    """
    t0 = time.perf_counter()
    chunks: list[str] = []
    timestamps: list[float] = []

    async for delta in stream_result.stream_text(delta=True, debounce_by=None):
        if delta:
            timestamps.append(time.perf_counter())
            chunks.append(delta)

    return "".join(chunks), _latency_from_timestamps(t0, timestamps)


async def collect_structured_streaming_latency(stream_result) -> tuple[object, StreamingLatency]:
    """Consume a structured StreamedRunResult via stream_output and collect latency metrics.

    Use for agents with structured output_type. Returns (parsed_output, StreamingLatency).
    """
    t0 = time.perf_counter()
    timestamps: list[float] = []
    output = None

    async for partial in stream_result.stream_output(debounce_by=None):
        timestamps.append(time.perf_counter())
        output = partial

    return output, _latency_from_timestamps(t0, timestamps)
