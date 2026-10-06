"""Connector routes."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_connector_service, get_tenant_context, TenantContext
from app.schemas.common import APIResponse
from app.schemas.connector import ConnectorCreate, ConnectorOut, ConnectorUpdate
from app.services.connector_service import ConnectorService

router = APIRouter()


@router.post("", response_model=APIResponse[ConnectorOut])
async def create_connector(
    body: ConnectorCreate,
    svc: ConnectorService = Depends(get_connector_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        connector = await svc.create(body, actor_id=tenant.actor_id, organization_id=tenant.organization_id)
        return APIResponse.ok(ConnectorOut.model_validate(connector))
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_CREATE_FAILED", str(exc))


@router.get("/pipeline/{pipeline_id}", response_model=APIResponse[list[ConnectorOut]])
async def list_connectors_by_pipeline(
    pipeline_id: UUID,
    svc: ConnectorService = Depends(get_connector_service),
):
    try:
        connectors = await svc.list_by_pipeline(pipeline_id)
        return APIResponse.ok([ConnectorOut.model_validate(c) for c in connectors])
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_LIST_FAILED", str(exc))


@router.get("/{connector_id}", response_model=APIResponse[ConnectorOut])
async def get_connector(
    connector_id: UUID,
    svc: ConnectorService = Depends(get_connector_service),
):
    try:
        connector = await svc.get(connector_id)
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        return APIResponse.ok(ConnectorOut.model_validate(connector))
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_GET_FAILED", str(exc))


@router.put("/{connector_id}", response_model=APIResponse[ConnectorOut])
async def update_connector(
    connector_id: UUID,
    body: ConnectorUpdate,
    svc: ConnectorService = Depends(get_connector_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        connector = await svc.update(
            connector_id, body, actor_id=tenant.actor_id, organization_id=tenant.organization_id
        )
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        return APIResponse.ok(ConnectorOut.model_validate(connector))
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_UPDATE_FAILED", str(exc))


@router.delete("/{connector_id}", response_model=APIResponse[dict])
async def delete_connector(
    connector_id: UUID,
    svc: ConnectorService = Depends(get_connector_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        deleted = await svc.delete(connector_id, actor_id=tenant.actor_id, organization_id=tenant.organization_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Connector not found")
        return APIResponse.ok({"id": str(connector_id), "deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_DELETE_FAILED", str(exc))


@router.post("/{connector_id}/sync", response_model=APIResponse[dict])
async def trigger_sync(
    connector_id: UUID,
    svc: ConnectorService = Depends(get_connector_service),
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        await svc.trigger_sync(connector_id, actor_id=tenant.actor_id, organization_id=tenant.organization_id)
        return APIResponse.ok({"id": str(connector_id), "sync_triggered": True})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        return APIResponse.fail("ERR_CONNECTOR_SYNC_FAILED", str(exc))
