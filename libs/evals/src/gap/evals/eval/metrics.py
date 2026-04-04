"""Content quality scoring — compares base and GAP output artifacts."""

from __future__ import annotations

import difflib
import re
from collections import Counter
from pathlib import Path

from ..models import ContentQualityScore, ExperimentQuality

_GAP_MARKER_RE = re.compile(r"</?gap:target[^>]*>")


def strip_gap_markers(text: str) -> str:
    """Remove all <gap:target ...> and </gap:target> tags."""
    return _GAP_MARKER_RE.sub("", text)


def _token_f1(a: str, b: str) -> float:
    """Word-token F1 score between two texts."""
    ta = Counter(a.lower().split())
    tb = Counter(b.lower().split())
    common = sum((ta & tb).values())
    if common == 0:
        return 0.0
    precision = common / max(sum(tb.values()), 1)
    recall = common / max(sum(ta.values()), 1)
    return 2 * precision * recall / (precision + recall)


def _diff_line_counts(a: str, b: str) -> tuple[int, int]:
    """Count lines added and removed between two texts."""
    diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
    added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    return added, removed


def _rouge_l(base: str, gap: str) -> float | None:
    """Compute ROUGE-L via ragas if available."""
    try:
        from ragas import SingleTurnSample
        from ragas.metrics import RougeScore

        scorer = RougeScore(rouge_type="rougeL")
        sample = SingleTurnSample(response=gap, reference=base)
        return scorer.single_turn_score(sample)
    except Exception:
        return None


def _bleu(base: str, gap: str) -> float | None:
    """Compute BLEU via ragas if available."""
    try:
        from ragas import SingleTurnSample
        from ragas.metrics import BleuScore

        scorer = BleuScore()
        sample = SingleTurnSample(response=gap, reference=base)
        return scorer.single_turn_score(sample)
    except Exception:
        return None


def score_turn(
    base_text: str,
    gap_text: str,
    turn: int,
    use_ragas: bool = False,
) -> ContentQualityScore:
    """Compute quality metrics for one turn pair."""
    gap_clean = strip_gap_markers(gap_text)
    seq_sim = difflib.SequenceMatcher(None, base_text, gap_clean).ratio()
    f1 = _token_f1(base_text, gap_clean)
    added, removed = _diff_line_counts(base_text, gap_clean)
    base_chars = len(base_text)
    gap_chars = len(gap_clean)
    delta_pct = ((gap_chars - base_chars) / base_chars * 100) if base_chars > 0 else 0.0

    rouge = _rouge_l(base_text, gap_clean) if use_ragas else None
    bleu = _bleu(base_text, gap_clean) if use_ragas else None

    return ContentQualityScore(
        turn=turn,
        sequence_similarity=round(seq_sim, 4),
        token_f1=round(f1, 4),
        base_char_count=base_chars,
        gap_char_count=gap_chars,
        char_delta_pct=round(delta_pct, 1),
        lines_added=added,
        lines_removed=removed,
        rouge_l=round(rouge, 4) if rouge is not None else None,
        bleu=round(bleu, 4) if bleu is not None else None,
    )


def score_experiment(
    base_output_dir: Path,
    gap_output_dir: Path,
    ext: str,
    use_ragas: bool = False,
) -> ExperimentQuality:
    """Score all turns for one experiment by reading artifacts from disk."""
    scores: list[ContentQualityScore] = []

    # Find matching turn files (turn-0, turn-1, ...)
    base_files = sorted(base_output_dir.glob(f"turn-*{ext}"))
    for bf in base_files:
        af = gap_output_dir / bf.name
        if not af.exists():
            continue
        turn_str = bf.stem.split("-")[1]
        turn = int(turn_str)
        scores.append(score_turn(bf.read_text(), af.read_text(), turn, use_ragas))

    if not scores:
        return ExperimentQuality(per_turn=[])

    mean_sim = sum(s.sequence_similarity for s in scores) / len(scores)
    mean_f1 = sum(s.token_f1 for s in scores) / len(scores)

    rouge_vals = [s.rouge_l for s in scores if s.rouge_l is not None]
    bleu_vals = [s.bleu for s in scores if s.bleu is not None]

    return ExperimentQuality(
        per_turn=scores,
        mean_sequence_similarity=round(mean_sim, 4),
        mean_token_f1=round(mean_f1, 4),
        mean_rouge_l=round(sum(rouge_vals) / len(rouge_vals), 4) if rouge_vals else None,
        mean_bleu=round(sum(bleu_vals) / len(bleu_vals), 4) if bleu_vals else None,
    )
