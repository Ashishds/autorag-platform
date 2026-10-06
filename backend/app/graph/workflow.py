"""build_optimization_graph() — Flow 3 only (LLD §7.3).

Conditional edges (MVP, no separate diagnoser node — Evaluator carries rule-based diagnosis):
    evaluator -> observer   (deploy_eligible)
    evaluator -> improver   (0.70 <= score < 0.85 AND faithfulness >= 0.50)
    evaluator -> END        (score < 0.70 OR faithfulness < 0.50 — hard block)
    observer  -> improver   (score_drift_detected)
    observer  -> END        (stable)
    improver  -> evaluator  (variant approved — re-eval on SAME golden_set_id)
    improver  -> END        (approval denied / no variant)
    evaluator -> deployer   (deploy_eligible after improvement)
    deployer  -> observer
"""

from __future__ import annotations

from app.constants import FAITHFULNESS_HARD_GATE, IMPROVE_SCORE_THRESHOLD
from app.graph.nodes import deployer_node, evaluator_node, improver_node, observer_node
from app.graph.state import OptimizationState


def _after_evaluator(state: OptimizationState) -> str:
    score = state.unified_score or 0.0
    faith = state.faithfulness_score or 0.0
    if faith < FAITHFULNESS_HARD_GATE or score < IMPROVE_SCORE_THRESHOLD:
        return "END"
    if state.deploy_eligible:
        return "deployer" if state.approved_variant else "observer"
    return "improver"


def _after_observer(state: OptimizationState) -> str:
    return "improver" if state.score_drift_detected else "END"


def _after_improver(state: OptimizationState) -> str:
    return "evaluator" if state.approved_variant else "END"


def build_optimization_graph(checkpointer=None):
    """Compile the optimization-loop graph. Requires `langgraph` to be installed."""
    from langgraph.graph import END, StateGraph

    g = StateGraph(OptimizationState)
    g.add_node("evaluator", evaluator_node)
    g.add_node("observer", observer_node)
    g.add_node("improver", improver_node)
    g.add_node("deployer", deployer_node)

    g.set_entry_point("evaluator")
    g.add_conditional_edges(
        "evaluator",
        _after_evaluator,
        {"observer": "observer", "improver": "improver", "deployer": "deployer", "END": END},
    )
    g.add_conditional_edges("observer", _after_observer, {"improver": "improver", "END": END})
    g.add_conditional_edges("improver", _after_improver, {"evaluator": "evaluator", "END": END})
    g.add_edge("deployer", "observer")

    return g.compile(checkpointer=checkpointer)
