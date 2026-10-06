"""Unified Score + deploy-decision tests (LLD §9.5)."""

from app.models import DeployDecision, EvalMetrics
from app.services.evaluation_service import EvaluationService


def test_unified_score_weights():
    svc = EvaluationService()
    m = EvalMetrics(retrieval=1.0, quality=1.0, faithfulness=1.0)
    # 0.25 + 0.35 + 0.25 = 0.85 (no penalties)
    assert round(svc.compute_unified_score(m), 4) == 0.85


def test_faithfulness_hard_gate_blocks():
    svc = EvaluationService()
    decision = svc.make_deploy_decision(score=0.99, faithfulness=0.4, adversarial_pass_rate=1.0)
    assert decision == DeployDecision.BLOCKED_FAITHFULNESS


def test_adversarial_anchor_must_be_perfect():
    svc = EvaluationService()
    decision = svc.make_deploy_decision(score=0.99, faithfulness=0.9, adversarial_pass_rate=0.8)
    assert decision == DeployDecision.BLOCKED_ADVERSARIAL


def test_deploy_when_eligible():
    svc = EvaluationService()
    decision = svc.make_deploy_decision(score=0.9, faithfulness=0.9, adversarial_pass_rate=1.0)
    assert decision == DeployDecision.DEPLOY


def test_improve_band():
    svc = EvaluationService()
    # Three-tier gate: DEPLOY >= 0.72, IMPROVE >= 0.60, else BLOCKED_SCORE.
    decision = svc.make_deploy_decision(score=0.65, faithfulness=0.9, adversarial_pass_rate=1.0)
    assert decision == DeployDecision.IMPROVE


def test_blocked_score_band():
    svc = EvaluationService()
    decision = svc.make_deploy_decision(score=0.55, faithfulness=0.9, adversarial_pass_rate=1.0)
    assert decision == DeployDecision.BLOCKED_SCORE
