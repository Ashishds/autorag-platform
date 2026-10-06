"""PipelineRepository — CRUD via supabase-py (LLD §5)."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class PipelineRepository(SupabaseRepository):
    TABLE = "pipelines"

    async def create(self, row: dict) -> dict:
        if self.client is not None:
            # Format UUIDs and dicts as strings for Supabase client
            res = (
                await self.client.table(self.TABLE)
                .insert(
                    {
                        "organization_id": str(row["organization_id"]),
                        "name": row["name"],
                        "description": row.get("description"),
                        "config": row["config"],
                        "chunking_strategy": row["chunking_strategy"],
                        "retrieval_method": row["retrieval_method"],
                        "llm_judge": row["llm_judge"],
                        "approval_mode": row["approval_mode"],
                        "status": row.get("status", "draft"),
                        "created_by": str(row["created_by"]),
                    }
                )
                .execute()
            )
            return res.data[0]

        # SQL fallback for local Postgres
        config_json = json.dumps(row["config"])
        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                INSERT INTO pipelines
                    (organization_id, name, description, config, chunking_strategy,
                     retrieval_method, llm_judge, approval_mode, status, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
                """,
                row["organization_id"],
                row["name"],
                row.get("description"),
                config_json,
                row["chunking_strategy"],
                row["retrieval_method"],
                row["llm_judge"],
                row["approval_mode"],
                row.get("status", "draft"),
                row["created_by"],
            )
            return self._process_record(r)

    async def get(self, pipeline_id: UUID) -> dict | None:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE).select("*").eq("id", str(pipeline_id)).execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM pipelines WHERE id = $1", pipeline_id)
            return self._process_record(r)

    async def list(self, organization_id: UUID) -> list[dict]:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("organization_id", str(organization_id))
                .execute()
            )
            return res.data

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM pipelines WHERE organization_id = $1", organization_id
            )
            return [self._process_record(r) for r in rows]

    async def set_active_version(self, pipeline_id: UUID, deployment_id: UUID) -> None:
        if self.client is not None:
            await (
                self.client.table(self.TABLE)
                .update({"active_version": str(deployment_id)})
                .eq("id", str(pipeline_id))
                .execute()
            )
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE pipelines SET active_version = $2, updated_at = NOW() WHERE id = $1",
                pipeline_id,
                deployment_id,
            )

    async def update(self, pipeline_id: UUID, row: dict) -> dict | None:
        if self.client is not None:
            upd = {}
            for k in ["name", "description", "chunking_strategy", "retrieval_method", "llm_judge", "approval_mode", "status"]:
                if k in row:
                    upd[k] = row[k]
            if "config" in row:
                upd["config"] = row["config"]
            
            if not upd:
                return await self.get(pipeline_id)
                
            res = (
                await self.client.table(self.TABLE)
                .update(upd)
                .eq("id", str(pipeline_id))
                .execute()
            )
            return res.data[0] if res.data else None

        # SQL fallback for local Postgres
        async with self.pool.acquire() as conn:
            fields = []
            values = []
            placeholder_idx = 1
            for k in ["name", "description", "chunking_strategy", "retrieval_method", "llm_judge", "approval_mode", "status"]:
                if k in row:
                    fields.append(f"{k} = ${placeholder_idx}")
                    values.append(row[k])
                    placeholder_idx += 1
            if "config" in row:
                fields.append(f"config = ${placeholder_idx}")
                values.append(json.dumps(row["config"]) if isinstance(row["config"], dict) else row["config"])
                placeholder_idx += 1
            
            if not fields:
                return await self.get(pipeline_id)

            values.append(pipeline_id)
            query = f"UPDATE pipelines SET {', '.join(fields)}, updated_at = NOW() WHERE id = ${placeholder_idx} RETURNING *"
            r = await conn.fetchrow(query, *values)
            return self._process_record(r)

    async def delete(self, pipeline_id: UUID) -> bool:
        """Hard-delete a pipeline and every row that references it.

        Done in one transaction over the asyncpg pool because the FKs to
        pipelines/pipeline_runs are NO ACTION (no cascade), so children must be
        removed first and in dependency order. Returns True if the pipeline row
        existed and was removed.
        """
        if self.pool is None:
            raise RuntimeError("pipeline delete requires a database pool")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                run_filter = "SELECT id FROM pipeline_runs WHERE pipeline_id = $1"
                await conn.execute(
                    f"DELETE FROM evaluations WHERE run_id IN ({run_filter})", pipeline_id
                )
                await conn.execute(
                    f"DELETE FROM experiments WHERE run_id IN ({run_filter}) "
                    f"OR parent_run_id IN ({run_filter})",
                    pipeline_id,
                )
                # Break the deployments self-reference before deleting the set.
                await conn.execute(
                    "UPDATE deployments SET previous_deployment = NULL WHERE pipeline_id = $1",
                    pipeline_id,
                )
                await conn.execute("DELETE FROM deployments WHERE pipeline_id = $1", pipeline_id)
                await conn.execute("DELETE FROM query_logs WHERE pipeline_id = $1", pipeline_id)
                await conn.execute("DELETE FROM golden_datasets WHERE pipeline_id = $1", pipeline_id)
                await conn.execute(
                    "DELETE FROM chunk_embeddings WHERE pipeline_id = $1", pipeline_id
                )
                await conn.execute("DELETE FROM documents WHERE pipeline_id = $1", pipeline_id)
                await conn.execute("DELETE FROM pipeline_runs WHERE pipeline_id = $1", pipeline_id)
                result = await conn.execute("DELETE FROM pipelines WHERE id = $1", pipeline_id)
        return result.rsplit(" ", 1)[-1] != "0"

    def _process_record(self, r) -> dict | None:
        if not r:
            return None
        data = dict(r)
        if "config" in data and isinstance(data["config"], str):
            try:
                data["config"] = json.loads(data["config"])
            except ValueError:
                pass
        return data
