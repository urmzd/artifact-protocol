"""LLM-as-judge scoring — evaluates whether an edit instruction was fulfilled."""

from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model

from ..models import JudgeScore, TurnJudgeComparison
from .metrics import strip_gap_markers

_JUDGE_SYSTEM = """\
You are evaluating whether a text artifact correctly implements an edit instruction.

Given the edit instruction and the resulting artifact, score how well the edit was fulfilled.

- Score 0.0 = the edit was not applied at all
- Score 0.5 = partially applied (some elements present, others missing)
- Score 1.0 = perfectly fulfilled

Focus ONLY on whether the specific changes requested are present in the output.
Do NOT penalize for differences in style, formatting, or structure.
Do NOT penalize for the presence of XML-like markers or annotations.
"""


class JudgeOutput(BaseModel):
    """Structured output from the judge LLM."""

    score: float = Field(ge=0.0, le=1.0, description="Edit fulfillment score")
    reasoning: str = Field(description="Brief explanation of the score")


async def judge_turn(
    model: Model,
    edit_instruction: str,
    artifact_text: str,
    flow: str,
    turn: int,
) -> JudgeScore:
    """Score a single turn's output against the edit instruction."""
    agent: Agent[None, JudgeOutput] = Agent(
        model,
        system_prompt=_JUDGE_SYSTEM,
        output_type=JudgeOutput,
    )

    user_msg = (
        f"## Edit Instruction\n\n{edit_instruction}\n\n"
        f"## Resulting Artifact\n\n```\n{artifact_text}\n```"
    )

    r = await agent.run(user_msg)
    out = r.output

    return JudgeScore(
        turn=turn,
        flow=flow,
        score=round(out.score, 4),
        reasoning=out.reasoning,
    )


async def judge_experiment(
    model: Model,
    exp_dir: Path,
    ext: str,
) -> list[TurnJudgeComparison]:
    """Judge all turns for one experiment, scoring both flows concurrently."""
    base_input = exp_dir / "inputs" / "base"
    base_output = exp_dir / "outputs" / "base"
    gap_output = exp_dir / "outputs" / "gap"

    # Find edit turn files (turn-1, turn-2, ... — skip turn-0 which is creation)
    turn_files = sorted(
        base_input.glob("turn-*.md"),
        key=lambda p: int(p.stem.split("-")[1]),
    )
    edit_turns = [tf for tf in turn_files if int(tf.stem.split("-")[1]) >= 1]

    comparisons: list[TurnJudgeComparison] = []

    for tf in edit_turns:
        turn_num = int(tf.stem.split("-")[1])
        edit_instruction = tf.read_text().strip()
        turn_name = tf.stem  # e.g. "turn-1"

        base_file = base_output / f"{turn_name}{ext}"
        gap_file = gap_output / f"{turn_name}{ext}"

        if not base_file.exists() or not gap_file.exists():
            continue

        base_text = base_file.read_text()
        gap_text = strip_gap_markers(gap_file.read_text())

        # Judge base and GAP concurrently
        base_score, gap_score = await asyncio.gather(
            judge_turn(model, edit_instruction, base_text, "base", turn_num),
            judge_turn(model, edit_instruction, gap_text, "gap", turn_num),
        )

        comparisons.append(TurnJudgeComparison(
            turn=turn_num,
            edit_instruction=edit_instruction[:120],
            base_score=base_score.score,
            gap_score=gap_score.score,
            base_reasoning=base_score.reasoning,
            gap_reasoning=gap_score.reasoning,
        ))

    return comparisons
