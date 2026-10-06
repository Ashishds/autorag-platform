"""PipelineService — CRUD orchestration over the pipeline repository."""

from __future__ import annotations

import uuid
from uuid import UUID

from app.schemas.pipeline import PipelineCreate, PipelineUpdate


class PipelineService:
    def __init__(self, pipeline_repo=None, audit=None):
        self._repo = pipeline_repo
        self._audit = audit

    async def create(self, data: PipelineCreate, created_by: UUID, organization_id: UUID):
        row = {
            "organization_id": organization_id,
            "name": data.name,
            "description": data.description,
            "chunking_strategy": data.chunking_strategy.value,
            "retrieval_method": data.retrieval_method.value,
            "llm_judge": data.llm_judge,
            "approval_mode": data.approval_mode.value,
            "config": data.config,
            "created_by": created_by,
        }
        pipeline = await self._repo.create(row)

        if self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="PIPELINE_CREATED",
                actor_id=created_by,
                resource_type="pipeline",
                resource_id=pipeline["id"],
                trace_id=trace_id,
                payload=pipeline,
            )
        return pipeline

    async def update(self, pipeline_id: UUID, data: PipelineUpdate, actor_id: UUID, organization_id: UUID):
        upd_data = {}
        if data.name is not None:
            upd_data["name"] = data.name
        if data.description is not None:
            upd_data["description"] = data.description
        if data.chunking_strategy is not None:
            upd_data["chunking_strategy"] = data.chunking_strategy.value
        if data.retrieval_method is not None:
            upd_data["retrieval_method"] = data.retrieval_method.value
        if data.llm_judge is not None:
            upd_data["llm_judge"] = data.llm_judge
        if data.approval_mode is not None:
            upd_data["approval_mode"] = data.approval_mode.value
        if data.config is not None:
            upd_data["config"] = data.config

        pipeline = await self._repo.update(pipeline_id, upd_data)

        if pipeline and self._audit is not None:
            trace_id = uuid.uuid4()
            await self._audit.log(
                organization_id=organization_id,
                event_type="PIPELINE_UPDATED",
                actor_id=actor_id,
                resource_type="pipeline",
                resource_id=pipeline_id,
                trace_id=trace_id,
                payload=pipeline,
            )
        return pipeline

    async def get(self, pipeline_id: UUID):
        return await self._repo.get(pipeline_id)

    async def list(self, organization_id: UUID):
        return await self._repo.list(organization_id)

    async def delete(self, pipeline_id: UUID) -> bool:
        return await self._repo.delete(pipeline_id)
