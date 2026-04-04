"""Evaluation orchestrator — text metrics + optional LLM judge."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai.models import Model

from ..models import ExperimentQuality
from .metrics import score_experiment


async def run_eval(
    exp_dir: Path,
    ext: str,
    use_ragas: bool = False,
    model: Model | None = None,
) -> ExperimentQuality:
    """Run all quality evaluations for one experiment.

    Returns an ExperimentQuality with text metrics and optional judge scores.
    """
    base_output = exp_dir / "outputs" / "base"
    gap_output = exp_dir / "outputs" / "gap"

    quality = score_experiment(base_output, gap_output, ext, use_ragas)

    if model is not None:
        from .judge import judge_experiment

        comparisons = await judge_experiment(model, exp_dir, ext)
        quality.judge_comparisons = comparisons

        if comparisons:
            quality.mean_base_judge = round(
                sum(c.base_score for c in comparisons) / len(comparisons), 4
            )
            quality.mean_gap_judge = round(
                sum(c.gap_score for c in comparisons) / len(comparisons), 4
            )

    return quality
