"""DeployService — MVP config activation + instant rollback (LLD §15)."""

from __future__ import annotations

from uuid import UUID


class DeployService:
    def __init__(self, deployment_repo=None, pipeline_repo=None, audit=None):
        self._deploy_repo = deployment_repo
        self._pipeline_repo = pipeline_repo
        self._audit = audit

    async def activate(
        self,
        pipeline_id: UUID,
        run_id: UUID,
        organization_id: UUID,
        config: dict,
        unified_score: float,
        environment: str = "production",
        actor_id: UUID | None = None,
    ) -> dict:
        dep = await self._deploy_repo.activate(
            pipeline_id=pipeline_id,
            run_id=run_id,
            organization_id=organization_id,
            config=config,
            unified_score=unified_score,
            environment=environment,
        )
        await self._pipeline_repo.set_active_version(pipeline_id, dep["id"])

        if self._audit is not None:
            import uuid

            await self._audit.log(
                organization_id=organization_id,
                event_type="PIPELINE_DEPLOYED",
                actor_id=actor_id or uuid.UUID(int=0),
                resource_type="deployment",
                resource_id=dep["id"],
                trace_id=uuid.uuid4(),
                payload={"pipeline_id": str(pipeline_id), "run_id": str(run_id)},
            )
        return dep

    async def rollback(
        self,
        pipeline_id: UUID,
        organization_id: UUID,
        reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> dict | None:
        active = await self._deploy_repo.get_active(pipeline_id)
        if not active:
            return None

        await self._deploy_repo.mark_rolled_back(active["id"], reason)
        previous_id = active.get("previous_deployment")
        if previous_id:
            await self._pipeline_repo.set_active_version(pipeline_id, previous_id)

        if self._audit is not None:
            import uuid

            await self._audit.log(
                organization_id=organization_id,
                event_type="PIPELINE_ROLLED_BACK",
                actor_id=actor_id or uuid.UUID(int=0),
                resource_type="deployment",
                resource_id=active["id"],
                trace_id=uuid.uuid4(),
                payload={"reason": reason, "pipeline_id": str(pipeline_id)},
            )
        return active
