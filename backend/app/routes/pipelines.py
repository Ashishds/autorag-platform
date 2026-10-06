"""Pipeline CRUD route — direct config (no wizard). LLD §6.2."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_pipeline_service, get_tenant_context, TenantContext
from app.schemas.common import APIResponse
from app.schemas.pipeline import PipelineCreate, PipelineOut, PipelineUpdate
from app.services.pipeline_service import PipelineService

router = APIRouter()


@router.post("", response_model=APIResponse[PipelineOut])
async def create_pipeline(
    body: PipelineCreate,
    svc: PipelineService = Depends(get_pipeline_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        pipeline = await svc.create(
            body, created_by=tenant.actor_id, organization_id=tenant.organization_id
        )
        return APIResponse.ok(PipelineOut.model_validate(pipeline))
    except Exception as exc:
        return APIResponse.fail("ERR_PIPELINE_CREATE_FAILED", str(exc))


@router.get("", response_model=APIResponse[list[PipelineOut]])
async def list_pipelines(
    svc: PipelineService = Depends(get_pipeline_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        pipelines = await svc.list(tenant.organization_id)
        return APIResponse.ok([PipelineOut.model_validate(p) for p in pipelines])
    except Exception as exc:
        return APIResponse.fail("ERR_PIPELINE_LIST_FAILED", str(exc))


@router.delete("/{pipeline_id}", response_model=APIResponse[dict])
async def delete_pipeline(
    pipeline_id: UUID,
    svc: PipelineService = Depends(get_pipeline_service),
):
    try:
        deleted = await svc.delete(pipeline_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return APIResponse.ok({"id": str(pipeline_id), "deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_PIPELINE_DELETE_FAILED", str(exc))


@router.get("/{pipeline_id}", response_model=APIResponse[PipelineOut])
async def get_pipeline(
    pipeline_id: UUID,
    svc: PipelineService = Depends(get_pipeline_service),
):
    try:
        pipeline = await svc.get(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return APIResponse.ok(PipelineOut.model_validate(pipeline))
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_PIPELINE_GET_FAILED", str(exc))


@router.put("/{pipeline_id}", response_model=APIResponse[PipelineOut])
async def update_pipeline(
    pipeline_id: UUID,
    body: PipelineUpdate,
    svc: PipelineService = Depends(get_pipeline_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        pipeline = await svc.update(
            pipeline_id, body, actor_id=tenant.actor_id, organization_id=tenant.organization_id
        )
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return APIResponse.ok(PipelineOut.model_validate(pipeline))
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_PIPELINE_UPDATE_FAILED", str(exc))
