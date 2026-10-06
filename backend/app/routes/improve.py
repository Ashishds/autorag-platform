"""Improve route — trigger variant generation for a run."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_run_repo
from app.repositories.run_repo import RunRepository
from app.schemas.common import APIResponse
from app.schemas.tasks import EvalTaskPayload
from app.workers.evaluate_task import run_evaluation

router = APIRouter()


@router.post("/{run_id}")
async def improve(
    run_id: UUID,
    run_repo: RunRepository = Depends(get_run_repo),
):
    run = await run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    pipeline_id = run["pipeline_id"]
    if isinstance(pipeline_id, str):
        pipeline_id = UUID(pipeline_id)

    org_id = run["organization_id"]
    if isinstance(org_id, str):
        org_id = UUID(org_id)

    new_run_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    await run_repo.create(
        {
            "id": new_run_id,
            "pipeline_id": pipeline_id,
            "organization_id": org_id,
            "trace_id": trace_id,
            "status": "pending",
            "triggered_by": "api",
            "metadata": {"parent_run_id": str(run_id), "improvement_trigger": True},
        }
    )

    run_evaluation.delay(
        EvalTaskPayload(
            pipeline_id=pipeline_id,
            organization_id=org_id,
            run_id=new_run_id,
            trace_id=trace_id,
        ).model_dump()
    )

    return APIResponse.ok(
        {"run_id": str(new_run_id), "status": "queued", "parent_run_id": str(run_id)}
    )
