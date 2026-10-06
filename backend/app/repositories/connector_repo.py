"""ConnectorRepository — CRUD for data_connectors."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class ConnectorRepository(SupabaseRepository):
    TABLE = "data_connectors"

    async def create(self, row: dict) -> dict:
        if self.client is not None:
            insert_data = {
                "organization_id": str(row["organization_id"]),
                "pipeline_id": str(row["pipeline_id"]),
                "name": row["name"],
                "type": row["type"],
                "config": row.get("config", {}),
                "sync_interval_minutes": row.get("sync_interval_minutes", 60),
            }
            if "id" in row:
                insert_data["id"] = str(row["id"])
            res = await self.client.table(self.TABLE).insert(insert_data).execute()
            return res.data[0]

        async with self.pool.acquire() as conn:
            if "id" in row:
                r = await conn.fetchrow(
                    """
                    INSERT INTO data_connectors
                        (id, organization_id, pipeline_id, name, type, config, sync_interval_minutes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    row["id"],
                    row["organization_id"],
                    row["pipeline_id"],
                    row["name"],
                    row["type"],
                    json.dumps(row.get("config", {})),
                    row.get("sync_interval_minutes", 60),
                )
            else:
                r = await conn.fetchrow(
                    """
                    INSERT INTO data_connectors
                        (id, organization_id, pipeline_id, name, type, config, sync_interval_minutes)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6)
                    RETURNING *
                    """,
                    row["organization_id"],
                    row["pipeline_id"],
                    row["name"],
                    row["type"],
                    json.dumps(row.get("config", {})),
                    row.get("sync_interval_minutes", 60),
                )
            # Need to parse jsonb back if we return it directly, asyncpg usually handles it.
            res_dict = dict(r) if r else None
            if res_dict and isinstance(res_dict.get('config'), str):
                res_dict['config'] = json.loads(res_dict['config'])
            return res_dict

    async def get(self, connector_id: UUID) -> dict | None:
        if self.client is not None:
            res = await self.client.table(self.TABLE).select("*").eq("id", str(connector_id)).execute()
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM data_connectors WHERE id = $1", connector_id)
            if r:
                res_dict = dict(r)
                if isinstance(res_dict.get('config'), str):
                    res_dict['config'] = json.loads(res_dict['config'])
                return res_dict
            return None

    async def list_by_pipeline(self, pipeline_id: UUID) -> list[dict]:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("pipeline_id", str(pipeline_id))
                .order("created_at", desc=True)
                .execute()
            )
            return res.data

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM data_connectors
                WHERE pipeline_id = $1
                ORDER BY created_at DESC
                """,
                pipeline_id,
            )
            res_list = []
            for r in rows:
                d = dict(r)
                if isinstance(d.get('config'), str):
                    d['config'] = json.loads(d['config'])
                res_list.append(d)
            return res_list
            
    async def list_active(self) -> list[dict]:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("status", "active")
                .execute()
            )
            return res.data

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM data_connectors WHERE status = 'active'")
            res_list = []
            for r in rows:
                d = dict(r)
                if isinstance(d.get('config'), str):
                    d['config'] = json.loads(d['config'])
                res_list.append(d)
            return res_list

    async def update(self, connector_id: UUID, updates: dict) -> dict | None:
        if "config" in updates and isinstance(updates["config"], dict) and self.client is None:
            updates["config"] = json.dumps(updates["config"])
            
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .update(updates)
                .eq("id", str(connector_id))
                .execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            set_clauses = []
            values = [connector_id]
            for i, (k, v) in enumerate(updates.items(), start=2):
                set_clauses.append(f"{k} = ${i}")
                values.append(v)
            
            if not set_clauses:
                return await self.get(connector_id)
                
            set_clauses.append("updated_at = NOW()")
            
            query = f"""
                UPDATE data_connectors
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING *
            """
            r = await conn.fetchrow(query, *values)
            if r:
                res_dict = dict(r)
                if isinstance(res_dict.get('config'), str):
                    res_dict['config'] = json.loads(res_dict['config'])
                return res_dict
            return None

    async def delete(self, connector_id: UUID) -> bool:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .delete()
                .eq("id", str(connector_id))
                .execute()
            )
            return bool(res.data)

        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM data_connectors WHERE id = $1", connector_id)
        return result.rsplit(" ", 1)[-1] != "0"
