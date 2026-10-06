"""Deployment contracts — config activation + instant rollback (LLD §6.2, §15)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class DeployRequest(BaseModel):
    pipeline_id: UUID
    run_id: UUID
    environment: str = "production"


class RollbackRequest(BaseModel):
    pipeline_id: UUID
    reason: str | None = None


class DeploymentOut(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: str
    strategy: str = "config_activation"
    unified_score: float
    previous_deployment: UUID | None = None
