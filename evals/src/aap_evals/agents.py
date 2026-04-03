"""Artifact generation and LLM model factory.

Uses pydantic-ai for LLM interaction with rate-limit retry.
"""

from __future__ import annotations

import re

import httpx
from httpx import HTTPStatusError
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import retry_if_exception_type, stop_after_attempt


# ── Rate-limit aware HTTP client ──────────────────────────────────────────


def _retrying_http_client() -> httpx.AsyncClient:
    """Create an httpx client that retries on 429/5xx with Retry-After backoff."""
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(HTTPStatusError),
            wait=wait_retry_after(max_wait=120),
            stop=stop_after_attempt(5),
            reraise=True,
        ),
        validate_response=lambda r: r.raise_for_status() if r.status_code in (429, 500, 502, 503) else None,
    )
    return httpx.AsyncClient(transport=transport, timeout=120)


# ── Provider defaults ─────────────────────────────────────────────────────

PROVIDER_DEFAULTS: dict[str, str] = {
    "google": "gemini-2.0-flash",
    "openai": "gpt-4o-mini",
    "ollama": "gemma4",
}


# ── Model factory ───────────────────────────────────────────────────────────


def _build_model(provider: str, model_name: str, host: str) -> Model:
    if provider == "google":
        return GoogleModel(
            model_name=model_name or PROVIDER_DEFAULTS["google"],
            provider=GoogleProvider(http_client=_retrying_http_client()),
        )
    elif provider == "openai":
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["openai"],
            provider=OpenAIProvider(),
        )
    elif provider == "ollama":
        base = host.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        return OpenAIChatModel(
            model_name=model_name or PROVIDER_DEFAULTS["ollama"],
            provider=OllamaProvider(base_url=base),
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
    secondary = _build_model(fallback, "", host)
    return FallbackModel(primary, secondary)


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


def generate_artifact(model: Model, prompt: str) -> str:
    """Generate a single artifact. Returns cleaned content."""
    agent: Agent[None, str] = Agent(
        model,
        system_prompt="You are a code generator. Output only raw code/content. No markdown fences, no explanation.",
    )
    result = agent.run_sync(prompt)
    return clean_artifact(result.output)
