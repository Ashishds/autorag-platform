"""DocumentRepository — document lifecycle / status state machine (LLD §3.10)."""

from __future__ import annotations

from uuid import UUID

from app.repositories.base import SupabaseRepository

VALID_STATUS = {"queued", "pre_processing", "processing", "completed", "failed", "cancelled"}


class DocumentRepository(SupabaseRepository):
    TABLE = "documents"

    async def create(self, row: dict) -> dict:
        filename_clean = row["filename"].replace("\x00", "").replace("\u0000", "")
        storage_path_clean = row["storage_path"].replace("\x00", "").replace("\u0000", "") if row.get("storage_path") else None
        if self.client is not None:
            insert_data = {
                "organization_id": str(row["organization_id"]),
                "pipeline_id": str(row["pipeline_id"]),
                "filename": filename_clean,
                "file_size": row["file_size"],
                "storage_path": storage_path_clean,
                "status": row.get("status", "queued"),
                "mime_type": row.get("mime_type"),
            }
            if "id" in row:
                insert_data["id"] = str(row["id"])
            res = await self.client.table(self.TABLE).insert(insert_data).execute()
            return res.data[0]

        async with self.pool.acquire() as conn:
            if "id" in row:
                r = await conn.fetchrow(
                    """
                    INSERT INTO documents
                        (id, organization_id, pipeline_id, filename, file_size, storage_path, status, mime_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING *
                    """,
                    row["id"],
                    row["organization_id"],
                    row["pipeline_id"],
                    filename_clean,
                    row["file_size"],
                    storage_path_clean,
                    row.get("status", "queued"),
                    row.get("mime_type"),
                )
            else:
                r = await conn.fetchrow(
                    """
                    INSERT INTO documents
                        (organization_id, pipeline_id, filename, file_size, storage_path, status, mime_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    row["organization_id"],
                    row["pipeline_id"],
                    filename_clean,
                    row["file_size"],
                    storage_path_clean,
                    row.get("status", "queued"),
                    row.get("mime_type"),
                )
            return dict(r) if r else None

    async def get(self, document_id: UUID) -> dict | None:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE).select("*").eq("id", str(document_id)).execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM documents WHERE id = $1", document_id)
            return dict(r) if r else None

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
                SELECT * FROM documents
                WHERE pipeline_id = $1
                ORDER BY created_at DESC
                """,
                pipeline_id,
            )
            return [dict(r) for r in rows]

    async def delete(self, document_id: UUID) -> bool:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .delete()
                .eq("id", str(document_id))
                .execute()
            )
            return bool(res.data)

        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
        return result.rsplit(" ", 1)[-1] != "0"

    async def set_status(
        self,
        document_id: UUID,
        status: str,
        error: str | None = None,
        chunk_count: int | None = None,
        pii_entities: int | None = None,
    ) -> None:
        assert status in VALID_STATUS, f"invalid document status: {status}"

        error_clean = error.replace("\x00", "").replace("\u0000", "") if error else None

        if self.client is not None:
            updates = {"status": status, "error": error_clean}
            if chunk_count is not None:
                updates["chunk_count"] = chunk_count
            if pii_entities is not None:
                updates["pii_entities"] = pii_entities
            await self.client.table(self.TABLE).update(updates).eq("id", str(document_id)).execute()
            return

        # SQL fallback for local Postgres
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE documents
                SET status = $2,
                    error = COALESCE($3, error),
                    chunk_count = COALESCE($4, chunk_count),
                    pii_entities = COALESCE($5, pii_entities),
                    updated_at = NOW()
                WHERE id = $1
                """,
                document_id,
                status,
                error_clean,
                chunk_count,
                pii_entities,
            )
