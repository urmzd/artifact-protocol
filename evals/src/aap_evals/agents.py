"""Baseline (full regen) vs AAP (context offloading) architectures.

Both use pydantic-ai. In the AAP flow, both init and maintain roles are
offloaded to ephemeral secondary contexts — the orchestrator never holds
full artifact content. The maintain context returns spec-compliant Envelope objects.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from .apply import apply_envelope
from .markers import marker_example
from .schema import Envelope


# ── Model factory ───────────────────────────────────────────────────────────


def create_model(provider: str, model_name: str, host: str) -> OpenAIChatModel:
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


def generate_artifact(model: OpenAIChatModel, prompt: str) -> str:
    """Generate a single artifact. Returns cleaned content."""
    agent: Agent[None, str] = Agent(
        model,
        system_prompt="You are a code generator. Output only raw code/content. No markdown fences, no explanation.",
    )
    result = agent.run_sync(prompt)
    return clean_artifact(result.output)


# ── Result types ────────────────────────────────────────────────────────────


@dataclass
class TurnResult:
    turn: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    output_bytes: int = 0
    envelope_name: str = ""
    envelope_parsed: bool = False
    apply_succeeded: bool = False

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "output_bytes": self.output_bytes,
            "envelope_name": self.envelope_name,
            "envelope_parsed": self.envelope_parsed,
            "apply_succeeded": self.apply_succeeded,
        }


@dataclass
class BaselineResult:
    turns: list[TurnResult] = field(default_factory=list)
    artifact: str = ""

    @property
    def total_input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.turns)

    @property
    def total_output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.turns)

    @property
    def total_latency_ms(self) -> int:
        return sum(t.latency_ms for t in self.turns)


@dataclass
class AAPResult:
    turns: list[TurnResult] = field(default_factory=list)
    artifact: str = ""

    @property
    def total_input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.turns)

    @property
    def total_output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.turns)

    @property
    def total_latency_ms(self) -> int:
        return sum(t.latency_ms for t in self.turns)

    @property
    def parse_rate(self) -> float:
        edits = [t for t in self.turns if t.turn > 0]
        return sum(1 for t in edits if t.envelope_parsed) / len(edits) if edits else 0

    @property
    def apply_rate(self) -> float:
        edits = [t for t in self.turns if t.turn > 0]
        return sum(1 for t in edits if t.apply_succeeded) / len(edits) if edits else 0


# ── Baseline flow (no offloading — growing conversation context) ───────────


def run_baseline(
    model: OpenAIChatModel,
    creation_prompt: str,
    edit_prompts: list[str],
    fmt: str,
) -> BaselineResult:
    """Baseline: growing conversation, full artifact regenerated each turn."""
    system = f"You produce {fmt} artifacts. Output raw code only. No markdown fences, no explanation."
    agent: Agent[None, str] = Agent(model, system_prompt=system)

    result = BaselineResult()
    history = None

    for i, prompt in enumerate([creation_prompt] + edit_prompts):
        t0 = time.perf_counter()
        if history is None:
            r = agent.run_sync(prompt)
        else:
            r = agent.run_sync(prompt, message_history=history)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        usage = r.usage()
        history = r.all_messages()
        artifact = r.output

        result.turns.append(TurnResult(
            turn=i,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_ms,
            output_bytes=len(artifact.encode()),
        ))

    result.artifact = artifact
    return result


# ── AAP flow (context offloading — ephemeral secondary contexts) ───────────


def run_aap(
    model: OpenAIChatModel,
    creation_prompt: str,
    edit_prompts: list[str],
    fmt: str,
    artifact_id: str = "artifact",
) -> AAPResult:
    """AAP: both init and maintain are offloaded to ephemeral secondary contexts.

    The orchestrator (this function) never holds artifact content in its own
    context — it dispatches to bounded secondary contexts and receives
    structured results (raw content from init, Envelope from maintain).
    """
    me = marker_example(fmt)

    # Init context: ephemeral, specialized for creation.
    # Receives only generation instructions. Returns raw artifact content.
    # Context is discarded after invocation.
    init_system = (
        f"You produce {fmt} artifacts with AAP section markers for incremental updates.\n\n"
        f"Wrap each major block with section markers: {me}\n\n"
        "Output raw code only. No markdown fences, no explanation."
    )

    # Maintain context: ephemeral, specialized for edits.
    # Receives only the current artifact + edit instruction. Returns Envelope.
    # Context is discarded after each invocation — no edit history accumulates.
    maintain_system = (
        f"You are an AAP maintain context. Given an artifact and an edit instruction, "
        f"return a JSON envelope to apply the change.\n\n"
        f"The artifact format is {fmt}.\n\n"
        f"Return a complete AAP envelope with protocol, id, version, name, operation, and content fields.\n"
        f'Use name "diff" for small text changes (search targeting).\n'
        f'Use name "section" for rewriting an entire section.\n\n'
        f"The search target in diff operations MUST be an exact substring from the artifact."
    )

    init_ctx: Agent[None, str] = Agent(model, system_prompt=init_system)
    maintain_ctx: Agent[None, Envelope] = Agent(
        model,
        system_prompt=maintain_system,
        output_type=Envelope,
    )

    result = AAPResult()

    # Turn 0: offload creation to init context (ephemeral, discarded after)
    t0 = time.perf_counter()
    r = init_ctx.run_sync(creation_prompt)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    usage = r.usage()
    artifact = clean_artifact(r.output)

    result.turns.append(TurnResult(
        turn=0,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=latency_ms,
        output_bytes=len(artifact.encode()),
    ))

    # Turns 1+: offload edits to maintain context (ephemeral, fresh each call)
    version = 1
    for i, edit in enumerate(edit_prompts):
        user_msg = f"## Current Artifact\n\n```\n{artifact}\n```\n\n## Edit Instruction\n\n{edit}"

        t0 = time.perf_counter()
        parsed = False
        succeeded = False
        env_name = ""

        try:
            r = maintain_ctx.run_sync(user_msg)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            usage = r.usage()

            envelope: Envelope = r.output
            parsed = True
            env_name = envelope.name

            # Apply the envelope
            new_artifact = apply_envelope(
                artifact, envelope.name, envelope.content, fmt,
            )
            succeeded = True
            artifact = new_artifact
            version += 1

        except Exception:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            usage = type("U", (), {"input_tokens": 0, "output_tokens": 0})()

        result.turns.append(TurnResult(
            turn=i + 1,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_ms,
            output_bytes=len(artifact.encode()),
            envelope_name=env_name,
            envelope_parsed=parsed,
            apply_succeeded=succeeded,
        ))

    result.artifact = artifact
    return result
