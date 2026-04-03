"""Artifact generation and LLM model factory.

Uses pydantic-ai for LLM interaction.
"""

from __future__ import annotations

import re

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider


# ── Model factory ───────────────────────────────────────────────────────────


def create_model(provider: str, model_name: str, host: str) -> Model:
    if provider == "ollama":
        base = host.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        return OpenAIChatModel(
            model_name=model_name or "gemma4",
            provider=OllamaProvider(base_url=base),
        )
    elif provider == "openai":
        return OpenAIChatModel(
            model_name=model_name or "gpt-4o-mini",
            provider=OpenAIProvider(),
        )
    elif provider == "google":
        return GoogleModel(
            model_name=model_name or "gemini-3.1-flash-lite-preview",
            provider=GoogleProvider(),
        )
    else:
        raise ValueError(f"unsupported provider: {provider}")


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
