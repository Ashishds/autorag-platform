"""ExperimentRepository — improver variants + approval state (LLD §3.6)."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class ExperimentRepository(SupabaseRepository):
    TABLE = "experiments"

    async def insert(self, row: dict) -> dict:
        if self.client is not None:
            payload = {
                "run_id": str(row["run_id"]),
                "organization_id": str(row["organization_id"]),
                "golden_set_id": str(row["golden_set_id"]),
                "variant_config": row["variant_config"],
                "score_delta": row.get("score_delta"),
                "improvement_type": row.get("improvement_type"),
                "approval_tier": row.get("approval_tier"),
                "approval_status": row.get("approval_status", "pending"),
            }
            if row.get("parent_run_id"):
                payload["parent_run_id"] = str(row["parent_run_id"])
            res = await self.client.table(self.TABLE).insert(payload).execute()
            return res.data[0]

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                INSERT INTO experiments
                    (run_id, organization_id, parent_run_id, golden_set_id,
                     variant_config, score_delta, improvement_type,
                     approval_tier, approval_status)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
                RETURNING *
                """,
                row["run_id"],
                row["organization_id"],
                row.get("parent_run_id"),
                row["golden_set_id"],
                json.dumps(row["variant_config"]),
                row.get("score_delta"),
                row.get("improvement_type"),
                row.get("approval_tier"),
                row.get("approval_status", "pending"),
            )
            return dict(r) if r else {}

    async def get(self, experiment_id: UUID) -> dict | None:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("id", str(experiment_id))
                .execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM experiments WHERE id = $1", experiment_id)
            return dict(r) if r else None

    async def list_for_pipeline(self, pipeline_id: UUID) -> list[dict]:
        if self.client is not None:
            # experiments has two FKs to pipeline_runs (run_id, parent_run_id);
            # disambiguate the embed to the run_id relationship explicitly.
            res = (
                await self.client.table(self.TABLE)
                .select("*, pipeline_runs!experiments_run_id_fkey!inner(pipeline_id)")
                .eq("pipeline_runs.pipeline_id", str(pipeline_id))
                .execute()
            )
            return res.data or []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT e.*
                FROM experiments e
                JOIN pipeline_runs r ON r.id = e.run_id
                WHERE r.pipeline_id = $1
                ORDER BY e.created_at DESC
                """,
                pipeline_id,
            )
            return [dict(r) for r in rows]

    async def set_approval(
        self, experiment_id: UUID, status: str, approved_by: UUID | None = None
    ) -> None:
        updates = {"approval_status": status}
        if approved_by:
            updates["approved_by"] = str(approved_by)

        if self.client is not None:
            await (
                self.client.table(self.TABLE).update(updates).eq("id", str(experiment_id)).execute()
            )
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE experiments
                SET approval_status = $2, approved_by = $3
                WHERE id = $1
                """,
                experiment_id,
                status,
                approved_by,
            )
