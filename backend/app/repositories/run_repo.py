"""PipelineRunRepository (LLD §3.3)."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class RunRepository(SupabaseRepository):
    TABLE = "pipeline_runs"

    async def create(self, row: dict) -> dict:
        if self.client is not None:
            payload = {
                "id": str(row["id"]),
                "pipeline_id": str(row["pipeline_id"]),
                "organization_id": str(row["organization_id"]),
                "trace_id": str(row["trace_id"]),
                "status": row.get("status", "pending"),
                "triggered_by": row.get("triggered_by", "api"),
                "metadata": row.get("metadata") or {},
            }
            res = await self.client.table(self.TABLE).insert(payload).execute()
            return res.data[0]

        metadata = row.get("metadata") or {}
        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                INSERT INTO pipeline_runs
                    (id, pipeline_id, organization_id, trace_id, status, triggered_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                RETURNING *
                """,
                row["id"],
                row["pipeline_id"],
                row["organization_id"],
                row["trace_id"],
                row.get("status", "pending"),
                row.get("triggered_by", "api"),
                json.dumps(metadata),
            )
            return dict(r) if r else {}

    async def get(self, run_id: UUID) -> dict | None:
        if self.client is not None:
            res = await self.client.table(self.TABLE).select("*").eq("id", str(run_id)).execute()
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM pipeline_runs WHERE id = $1", run_id)
            return dict(r) if r else None

    async def list_by_pipeline(self, pipeline_id: UUID, limit: int = 25) -> list[dict]:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("pipeline_id", str(pipeline_id))
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM pipeline_runs
                WHERE pipeline_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                pipeline_id,
                limit,
            )
            return [dict(r) for r in rows]

    async def update_status(self, run_id: UUID, status: str, **fields) -> None:
        updates = {"status": status, **fields}
        if self.client is not None:
            payload = {k: (str(v) if isinstance(v, UUID) else v) for k, v in updates.items()}
            if "metadata" in payload and isinstance(payload["metadata"], dict):
                payload["metadata"] = payload["metadata"]
            await self.client.table(self.TABLE).update(payload).eq("id", str(run_id)).execute()
            return

        set_clauses = ["status = $2"]
        values: list = [run_id, status]
        idx = 3
        for key, val in fields.items():
            if key == "metadata":
                set_clauses.append(f"{key} = ${idx}::jsonb")
                values.append(json.dumps(val))
            else:
                set_clauses.append(f"{key} = ${idx}")
                values.append(val)
            idx += 1

        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE pipeline_runs SET {', '.join(set_clauses)} WHERE id = $1",
                *values,
            )
