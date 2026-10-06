"""Experiments route — list variants + approval state."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_experiment_repo
from app.repositories.experiment_repo import ExperimentRepository
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("")
async def list_experiments(
    pipeline_id: UUID,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    rows = await exp_repo.list_for_pipeline(pipeline_id)
    return APIResponse.ok(rows)
