"""Evaluate route — enqueues the optimization-loop evaluation."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_pipeline_repo, get_run_repo
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.run_repo import RunRepository
from app.schemas.common import APIResponse
from app.schemas.evaluation import EvaluateRequest
from app.schemas.tasks import EvalTaskPayload
from app.workers.evaluate_task import dispatch_evaluation

router = APIRouter()


@router.post("")
async def evaluate(
    body: EvaluateRequest,
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
    run_repo: RunRepository = Depends(get_run_repo),
):
    pipeline = await pipeline_repo.get(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    run_id = body.run_id or uuid.uuid4()
    trace_id = uuid.uuid4()
    organization_id = pipeline["organization_id"]
    if isinstance(organization_id, str):
        organization_id = uuid.UUID(organization_id)

    await run_repo.create(
        {
            "id": run_id,
            "pipeline_id": body.pipeline_id,
            "organization_id": organization_id,
            "trace_id": trace_id,
            "status": "pending",
            "triggered_by": "api",
        }
    )

    payload = EvalTaskPayload(
        pipeline_id=body.pipeline_id,
        organization_id=organization_id,
        run_id=run_id,
        trace_id=trace_id,
        adversarial_dynamic_count=body.adversarial_dynamic_count,
    )
    dispatch_evaluation(payload)

    run = await run_repo.get(run_id)
    status = run["status"] if run else "queued"

    golden_set_id = uuid.uuid4()
    return APIResponse.ok(
        {
            "job_id": str(run_id),
            "run_id": str(run_id),
            "golden_set_id": str(golden_set_id),
            "status": status,
        }
    )
