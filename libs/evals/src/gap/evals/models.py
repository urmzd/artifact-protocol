"""Shared result types for the eval system."""

from __future__ import annotations

from pydantic import BaseModel


class TurnResult(BaseModel):
    """Token usage and outcome for a single turn."""

    turn: int
    edit: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    output_bytes: int = 0
    ttft_ms: int | None = None
    ttlt_ms: int | None = None
    median_itl_ms: float | None = None
    failed: bool = False
    failure_reason: str = ""


class BaseTurnResult(TurnResult):
    pass


class GAPTurnResult(TurnResult):
    envelope_parsed: bool = False
    apply_succeeded: bool = False
    envelope_name: str = ""


class ContentQualityScore(BaseModel):
    """Per-turn content quality comparison."""

    turn: int
    sequence_similarity: float = 0.0
    token_f1: float = 0.0
    base_char_count: int = 0
    gap_char_count: int = 0
    char_delta_pct: float = 0.0
    lines_added: int = 0
    lines_removed: int = 0
    rouge_l: float | None = None
    bleu: float | None = None


class JudgeScore(BaseModel):
    """LLM-as-judge score for a single turn."""

    turn: int
    flow: str  # "base" or "gap"
    score: float  # 0.0 to 1.0
    reasoning: str = ""


class TurnJudgeComparison(BaseModel):
    """Side-by-side judge scores for one turn."""

    turn: int
    edit_instruction: str = ""
    base_score: float = 0.0
    gap_score: float = 0.0
    base_reasoning: str = ""
    gap_reasoning: str = ""


class ExperimentQuality(BaseModel):
    """Quality scores across all turns for one experiment."""

    per_turn: list[ContentQualityScore]
    mean_sequence_similarity: float = 0.0
    mean_token_f1: float = 0.0
    mean_rouge_l: float | None = None
    mean_bleu: float | None = None
    judge_comparisons: list[TurnJudgeComparison] | None = None
    mean_base_judge: float | None = None
    mean_gap_judge: float | None = None


# ── Format utilities ──────────────────────────────────────────────────────

FORMAT_TO_EXT: dict[str, str] = {
    "text/html": ".html",
    "text/x-python": ".py",
    "application/javascript": ".js",
    "text/typescript": ".ts",
    "application/json": ".json",
    "text/x-yaml": ".yaml",
    "text/x-toml": ".toml",
    "text/x-rust": ".rs",
    "text/x-go": ".go",
    "text/css": ".css",
    "text/x-shellscript": ".sh",
    "text/markdown": ".md",
    "image/svg+xml": ".svg",
    "application/xml": ".xml",
    "text/x-java": ".java",
    "text/x-ruby": ".rb",
    "application/sql": ".sql",
}
