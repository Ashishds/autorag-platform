"""Deploy + rollback routes — config activation (LLD §15)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_deploy_service, get_evaluation_repo, get_pipeline_repo
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.schemas.common import APIResponse
from app.schemas.deployment import DeploymentOut, DeployRequest, RollbackRequest
from app.services.deploy_service import DeployService

router = APIRouter()


@router.post("")
async def deploy(
    body: DeployRequest,
    deploy_svc: DeployService = Depends(get_deploy_service),
    eval_repo: EvaluationRepository = Depends(get_evaluation_repo),
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
):
    pipeline = await pipeline_repo.get(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    evaluation = await eval_repo.get_by_run_id(body.run_id)
    if not evaluation or not evaluation.get("deploy_eligible"):
        return APIResponse.fail(
            "ERR_EVAL_HARD_GATE",
            "Run is not deploy-eligible (score/faithfulness/adversarial gate)",
        )

    org_id = pipeline["organization_id"]
    if isinstance(org_id, str):
        org_id = uuid.UUID(org_id)

    config = pipeline.get("config") or {}
    dep = await deploy_svc.activate(
        pipeline_id=body.pipeline_id,
        run_id=body.run_id,
        organization_id=org_id,
        config=config,
        unified_score=float(evaluation["unified_score"]),
        environment=body.environment,
    )
    return APIResponse.ok(DeploymentOut.model_validate(dep))


@router.post("/rollback")
async def rollback(
    body: RollbackRequest,
    deploy_svc: DeployService = Depends(get_deploy_service),
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
):
    pipeline = await pipeline_repo.get(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    org_id = pipeline["organization_id"]
    if isinstance(org_id, str):
        org_id = uuid.UUID(org_id)

    dep = await deploy_svc.rollback(body.pipeline_id, org_id, reason=body.reason)
    if not dep:
        return APIResponse.fail("ERR_NO_ACTIVE_DEPLOYMENT", "No active deployment to rollback")
    return APIResponse.ok({"deployment_id": str(dep["id"]), "status": "rolled_back"})
