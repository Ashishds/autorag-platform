"""Observer node — drift detection (invoked by scheduled cron for MVP) (LLD §8.3, §16)."""

from __future__ import annotations

from app.db import get_pool, get_supabase
from app.graph.state import OptimizationState
from app.repositories.evaluation_repo import EvaluationRepository
from app.services.observer_service import detect_score_drift


async def observer_node(state: OptimizationState) -> OptimizationState:
    supabase = None
    try:
        supabase = get_supabase()
    except RuntimeError:
        pass
    eval_repo = EvaluationRepository(supabase, pool=get_pool())

    history = await eval_repo.list_scores_for_pipeline(state.pipeline_id, limit=10)
    if len(history) >= 2 and state.unified_score is not None:
        prior = [float(r["unified_score"]) for r in history[1:]]
        state.score_drift_detected = detect_score_drift(state.unified_score, prior)
    else:
        state.score_drift_detected = False

    state.current_agent = "observer"
    return state
