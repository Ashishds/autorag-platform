"""Score route — returns the latest Unified Score breakdown for a run."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_evaluation_repo, get_run_repo
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.run_repo import RunRepository
from app.schemas.common import APIResponse
from app.schemas.evaluation import EvaluationResult, RagasScores

router = APIRouter()


@router.get("/{run_id}")
async def get_score(
    run_id: UUID,
    eval_repo: EvaluationRepository = Depends(get_evaluation_repo),
    run_repo: RunRepository = Depends(get_run_repo),
):
    run = await run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.get("status") in ("pending", "running"):
        return APIResponse.ok({"run_id": str(run_id), "status": run["status"]})

    row = await eval_repo.get_by_run_id(run_id)
    if not row:
        if run.get("status") == "failed":
            return APIResponse.fail(
                "ERR_EVAL_FAILED",
                run.get("error_message") or "Evaluation failed",
            )
        return APIResponse.ok({"run_id": str(run_id), "status": run.get("status", "unknown")})

    result = EvaluationResult(
        run_id=run_id,
        golden_set_id=UUID(str(row["golden_set_id"])),
        unified_score=float(row["unified_score"]),
        retrieval_score=float(row["retrieval_score"]),
        quality_score=float(row["quality_score"]),
        faithfulness_score=float(row["faithfulness_score"]),
        latency_penalty=float(row.get("latency_penalty") or 0),
        cost_penalty=float(row.get("cost_penalty") or 0),
        ragas=RagasScores(
            context_precision=float(row["ragas_context_precision"])
            if row.get("ragas_context_precision") is not None
            else None,
            context_recall=float(row["ragas_context_recall"])
            if row.get("ragas_context_recall") is not None
            else None,
            answer_faithfulness=float(row["ragas_answer_faithfulness"])
            if row.get("ragas_answer_faithfulness") is not None
            else None,
            answer_relevancy=float(row["ragas_answer_relevancy"])
            if row.get("ragas_answer_relevancy") is not None
            else None,
        ),
        ragas_scorer=row.get("ragas_scorer") or "gemini-2.5-pro",
        adversarial_pass_rate=float(row["adversarial_pass_rate"])
        if row.get("adversarial_pass_rate") is not None
        else None,
        deploy_eligible=bool(row.get("deploy_eligible")),
        diagnosis=(run.get("metadata") or {}).get("diagnosis", []),
        judge_reasoning=row.get("judge_reasoning"),
    )
    return APIResponse.ok(result)
