"""Drift detection helpers shared by Observer node and cron (LLD §8.3, §16)."""

from __future__ import annotations

from app.constants import DRIFT_THRESHOLD


def detect_score_drift(latest: float, prior_scores: list[float]) -> bool:
    """True when latest dropped more than DRIFT_THRESHOLD below the rolling average."""
    if not prior_scores:
        return False
    avg = sum(prior_scores) / len(prior_scores)
    return latest < avg - DRIFT_THRESHOLD
