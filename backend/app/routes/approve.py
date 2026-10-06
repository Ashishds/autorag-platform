"""Approval route — grant/deny an experiment variant (LLD §14)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_approval_service, get_experiment_repo
from app.repositories.experiment_repo import ExperimentRepository
from app.schemas.common import APIResponse
from app.services.approval_service import ApprovalService

router = APIRouter()


class ApprovalDecision(BaseModel):
    approve: bool
    reviewer_id: UUID
    note: str | None = None


@router.post("/{experiment_id}")
async def approve(
    experiment_id: UUID,
    body: ApprovalDecision,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    approval_svc: ApprovalService = Depends(get_approval_service),
):
    experiment = await exp_repo.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    status = "approved" if body.approve else "rejected"
    await exp_repo.set_approval(experiment_id, status, approved_by=body.reviewer_id)

    return APIResponse.ok(
        {
            "experiment_id": str(experiment_id),
            "approval_status": status,
            "variant_config": experiment.get("variant_config"),
        }
    )
