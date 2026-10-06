"""Diagnose route — MVP returns rule-based hints from the Evaluator (LLM Diagnoser = P2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_run_repo
from app.repositories.run_repo import RunRepository
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/{run_id}")
async def diagnose(
    run_id: UUID,
    run_repo: RunRepository = Depends(get_run_repo),
):
    run = await run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    metadata = run.get("metadata") or {}
    diagnosis = metadata.get("diagnosis", [])
    return APIResponse.ok({"run_id": str(run_id), "diagnosis": diagnosis})
