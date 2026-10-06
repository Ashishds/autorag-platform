"""DeploymentRepository — config activation rows (LLD §3.7, §15)."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class DeploymentRepository(SupabaseRepository):
    TABLE = "deployments"

    async def activate(
        self,
        pipeline_id: UUID,
        run_id: UUID,
        organization_id: UUID,
        config: dict,
        unified_score: float,
        environment: str = "production",
    ) -> dict:
        previous = await self.get_active(pipeline_id)
        prev_id = previous["id"] if previous else None

        if self.client is not None:
            payload = {
                "pipeline_id": str(pipeline_id),
                "run_id": str(run_id),
                "organization_id": str(organization_id),
                "config_snapshot": config,
                "previous_deployment": str(prev_id) if prev_id else None,
                "environment": environment,
                "status": "active",
                "unified_score": unified_score,
            }
            res = await self.client.table(self.TABLE).insert(payload).execute()
            if prev_id:
                await (
                    self.client.table(self.TABLE)
                    .update({"status": "superseded"})
                    .eq("id", str(prev_id))
                    .execute()
                )
            return res.data[0]

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                if prev_id:
                    await conn.execute(
                        "UPDATE deployments SET status = 'superseded' WHERE id = $1",
                        prev_id,
                    )
                r = await conn.fetchrow(
                    """
                    INSERT INTO deployments
                        (pipeline_id, run_id, organization_id, config_snapshot,
                         previous_deployment, environment, status, unified_score)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6, 'active', $7)
                    RETURNING *
                    """,
                    pipeline_id,
                    run_id,
                    organization_id,
                    json.dumps(config),
                    prev_id,
                    environment,
                    unified_score,
                )
                return dict(r) if r else {}

    async def get_active(self, pipeline_id: UUID) -> dict | None:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("pipeline_id", str(pipeline_id))
                .eq("status", "active")
                .order("activated_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                SELECT * FROM deployments
                WHERE pipeline_id = $1 AND status = 'active'
                ORDER BY activated_at DESC
                LIMIT 1
                """,
                pipeline_id,
            )
            return dict(r) if r else None

    async def list_active(self) -> list[dict]:
        """All currently active deployments (one per pipeline at most)."""
        if self.client is not None:
            res = await self.client.table(self.TABLE).select("*").eq("status", "active").execute()
            return res.data or []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM deployments WHERE status = 'active' ORDER BY activated_at DESC"
            )
            return [dict(r) for r in rows]

    async def mark_rolled_back(self, deployment_id: UUID, reason: str | None) -> None:
        if self.client is not None:
            await (
                self.client.table(self.TABLE)
                .update({"status": "rolled_back", "rollback_reason": reason})
                .eq("id", str(deployment_id))
                .execute()
            )
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE deployments
                SET status = 'rolled_back', rollback_reason = $2
                WHERE id = $1
                """,
                deployment_id,
                reason,
            )
