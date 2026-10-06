"""AuditRepository — INSERT-ONLY (LLD §3.8, §9.7)."""

from __future__ import annotations

import json
from uuid import UUID

from app.repositories.base import SupabaseRepository


class AuditRepository(SupabaseRepository):
    TABLE = "audit_log"

    async def insert(
        self,
        organization_id: UUID,
        event_type: str,
        actor_id: UUID,
        resource_type: str,
        resource_id: UUID,
        trace_id: UUID,
        payload: dict,
    ) -> UUID:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .insert(
                    {
                        "organization_id": str(organization_id),
                        "event_type": event_type,
                        "actor_id": str(actor_id),
                        "resource_type": resource_type,
                        "resource_id": str(resource_id),
                        "trace_id": str(trace_id),
                        "payload": payload,
                    }
                )
                .execute()
            )
            return UUID(res.data[0]["id"])

        # SQL fallback for local Postgres
        payload_json = json.dumps(payload, default=str)
        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                INSERT INTO audit_log
                    (organization_id, event_type, actor_id, resource_type, resource_id, trace_id, payload)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                organization_id,
                event_type,
                actor_id,
                resource_type,
                resource_id,
                trace_id,
                payload_json,
            )
            return r["id"] if r else None
