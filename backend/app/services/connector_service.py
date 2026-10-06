"""ConnectorService — Orchestration over connector_repo."""

from __future__ import annotations

import uuid
from uuid import UUID

from app.schemas.connector import ConnectorCreate, ConnectorUpdate
from app.workers.connector_task import sync_connector_job


class ConnectorService:
    def __init__(self, connector_repo=None, audit=None):
        self._repo = connector_repo
        self._audit = audit

    async def create(self, data: ConnectorCreate, actor_id: UUID, organization_id: UUID):
        # Additional validation could be added here (e.g., verifying S3 credentials)
        row = {
            "organization_id": organization_id,
            "pipeline_id": data.pipeline_id,
            "name": data.name,
            "type": data.type.value,
            "config": data.config,
            "sync_interval_minutes": data.sync_interval_minutes,
        }
        connector = await self._repo.create(row)

        if self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="CONNECTOR_CREATED",
                actor_id=actor_id,
                resource_type="connector",
                resource_id=connector["id"],
                trace_id=trace_id,
                payload=connector,
            )
        return connector

    async def update(self, connector_id: UUID, data: ConnectorUpdate, actor_id: UUID, organization_id: UUID):
        upd_data = {}
        if data.name is not None:
            upd_data["name"] = data.name
        if data.config is not None:
            upd_data["config"] = data.config
        if data.sync_interval_minutes is not None:
            upd_data["sync_interval_minutes"] = data.sync_interval_minutes
        if data.status is not None:
            upd_data["status"] = data.status.value

        connector = await self._repo.update(connector_id, upd_data)

        if connector and self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="CONNECTOR_UPDATED",
                actor_id=actor_id,
                resource_type="connector",
                resource_id=connector_id,
                trace_id=trace_id,
                payload=connector,
            )
        return connector

    async def get(self, connector_id: UUID):
        return await self._repo.get(connector_id)

    async def list_by_pipeline(self, pipeline_id: UUID):
        return await self._repo.list_by_pipeline(pipeline_id)

    async def delete(self, connector_id: UUID, actor_id: UUID, organization_id: UUID) -> bool:
        success = await self._repo.delete(connector_id)
        if success and self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="CONNECTOR_DELETED",
                actor_id=actor_id,
                resource_type="connector",
                resource_id=connector_id,
                trace_id=trace_id,
                payload={"connector_id": str(connector_id)},
            )
        return success

    async def trigger_sync(self, connector_id: UUID, actor_id: UUID, organization_id: UUID) -> None:
        """Trigger a manual synchronization task for the connector."""
        connector = await self.get(connector_id)
        if not connector:
            raise ValueError(f"Connector {connector_id} not found")
        
        # Dispatch Celery task
        sync_connector_job.delay(str(connector_id))
        
        if self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="CONNECTOR_SYNC_TRIGGERED",
                actor_id=actor_id,
                resource_type="connector",
                resource_id=connector_id,
                trace_id=trace_id,
                payload={"connector_id": str(connector_id)},
            )
