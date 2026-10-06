"""Evaluator node — scores vs frozen golden set + rule-based diagnosis (LLD §8.3)."""

from __future__ import annotations

from app.db import get_pool, get_supabase
from app.graph.state import OptimizationState
from app.models import DeployDecision
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.golden_repo import GoldenRepository
from app.repositories.query_log_repo import QueryLogRepository
from app.services.embedding import get_embedding_provider
from app.services.evaluation_service import EvaluationService
from app.services.golden_set_service import GoldenSetService
from app.services.llm.service import LLMService
from app.services.query_service import QueryService
from app.services.reranker.cohere import CohereReranker


def _build_services():
    pool = get_pool()
    supabase = None
    try:
        supabase = get_supabase()
    except RuntimeError:
        pass
    chunk_repo = ChunkRepository(pool)
    golden_repo = GoldenRepository(supabase, pool=pool)
    eval_repo = EvaluationRepository(supabase, pool=pool)
    llm = LLMService()
    query_svc = QueryService(
        llm=llm,
        embedder=get_embedding_provider(),
        reranker=CohereReranker(),
        chunk_repo=chunk_repo,
        query_log_repo=QueryLogRepository(pool),
    )
    golden_svc = GoldenSetService(golden_repo=golden_repo, chunk_repo=chunk_repo, llm=llm)
    return golden_svc, query_svc, llm, eval_repo


async def evaluator_node(state: OptimizationState) -> OptimizationState:
    eval_svc = EvaluationService()
    golden_svc, query_svc, llm, eval_repo = _build_services()

    golden_qas, golden_set_id = await golden_svc.get_or_create_static_set(
        state.pipeline_id, state.organization_id
    )
    state.golden_set_id = golden_set_id

    result = await eval_svc.run_evaluation(
        state.pipeline_id,
        state.organization_id,
        golden_qas,
        query_svc,
        llm,
    )

    state.unified_score = result.unified_score
    state.retrieval_score = result.retrieval_score
    state.quality_score = result.quality_score
    state.faithfulness_score = result.faithfulness_score
    state.latency_penalty = result.latency_penalty
    state.cost_penalty = result.cost_penalty
    state.ragas_scores = result.ragas_scores
    state.ragas_scorer = result.ragas_scorer
    state.adversarial_pass_rate = result.adversarial_pass_rate
    state.deploy_eligible = result.deploy_eligible
    state.judge_reasoning = result.judge_reasoning
    state.diagnosis = result.diagnosis

    await eval_repo.insert(
        {
            "run_id": state.run_id,
            "organization_id": state.organization_id,
            "golden_set_id": golden_set_id,
            "unified_score": result.unified_score,
            "retrieval_score": result.retrieval_score,
            "quality_score": result.quality_score,
            "faithfulness_score": result.faithfulness_score,
            "latency_penalty": result.latency_penalty,
            "cost_penalty": result.cost_penalty,
            "ragas_context_precision": result.ragas_scores.get("context_precision"),
            "ragas_context_recall": result.ragas_scores.get("context_recall"),
            "ragas_answer_faithfulness": result.ragas_scores.get("answer_faithfulness"),
            "ragas_answer_relevancy": result.ragas_scores.get("answer_relevancy"),
            "ragas_scorer": result.ragas_scorer,
            "adversarial_pass_rate": result.adversarial_pass_rate,
            "adversarial_fail_count": result.adversarial_fail_count,
            "deploy_eligible": result.deploy_eligible,
            "failure_reason": result.deploy_decision.value
            if result.deploy_decision not in (DeployDecision.DEPLOY, DeployDecision.IMPROVE)
            else None,
            "judge_reasoning": result.judge_reasoning,
            "eval_duration_ms": result.eval_duration_ms,
        }
    )

    state.current_agent = "evaluator"
    return state
