"""Drift detection unit tests."""

from app.services.observer_service import detect_score_drift


def test_no_drift_when_scores_stable():
    assert not detect_score_drift(0.85, [0.84, 0.86, 0.85])


def test_drift_when_score_drops_sharply():
    assert detect_score_drift(0.70, [0.85, 0.86, 0.84])


def test_no_drift_with_empty_history():
    assert not detect_score_drift(0.70, [])
