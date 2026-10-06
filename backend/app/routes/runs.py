"""Runs route — lists evaluation runs for a pipeline (dashboard dropdowns)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_evaluation_repo, get_run_repo
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.run_repo import RunRepository
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("")
async def list_runs(
    pipeline_id: UUID,
    run_repo: RunRepository = Depends(get_run_repo),
    eval_repo: EvaluationRepository = Depends(get_evaluation_repo),
):
    try:
        runs = await run_repo.list_by_pipeline(pipeline_id)
        out = []
        for run in runs:
            run_id = UUID(str(run["id"]))
            unified_score = None
            deploy_eligible = False
            evaluation = await eval_repo.get_by_run_id(run_id)
            if evaluation:
                if evaluation.get("unified_score") is not None:
                    unified_score = float(evaluation["unified_score"])
                deploy_eligible = bool(evaluation.get("deploy_eligible"))
            out.append(
                {
                    "run_id": str(run_id),
                    "status": run.get("status"),
                    "triggered_by": run.get("triggered_by"),
                    "created_at": str(run.get("created_at")) if run.get("created_at") else None,
                    "unified_score": unified_score,
                    "deploy_eligible": deploy_eligible,
                }
            )
        return APIResponse.ok(out)
    except Exception as exc:
        return APIResponse.fail("ERR_RUNS_LIST_FAILED", str(exc))
