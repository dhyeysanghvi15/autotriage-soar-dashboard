from __future__ import annotations

from autotriage.core.models.case import ScoreContribution, ScoreExplanation


def make_explanation(
    *, severity: int, confidence: float, contributions: list[ScoreContribution]
) -> ScoreExplanation:
    return ScoreExplanation(severity=severity, confidence=confidence, contributions=contributions)

