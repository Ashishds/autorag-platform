"""GoldenDatasetRepository — frozen static Q&A set (LLD §3.5)."""

from __future__ import annotations

from uuid import UUID

from app.repositories.base import SupabaseRepository


class GoldenRepository(SupabaseRepository):
    TABLE = "golden_datasets"

    async def get_for_pipeline(self, pipeline_id: UUID) -> list[dict]:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("pipeline_id", str(pipeline_id))
                .order("created_at")
                .execute()
            )
            return res.data or []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM golden_datasets WHERE pipeline_id = $1 ORDER BY created_at",
                pipeline_id,
            )
            return [dict(r) for r in rows]

    async def bulk_insert(self, rows: list[dict]) -> int:
        if not rows:
            return 0

        if self.client is not None:
            payload = [
                {
                    "pipeline_id": str(r["pipeline_id"]),
                    "organization_id": str(r["organization_id"]),
                    "question": r["question"],
                    "expected_answer": r.get("expected_answer"),
                    "expected_chunks": [str(c) for c in r.get("expected_chunks") or []],
                    "question_type": r["question_type"],
                    "set_version": r.get("set_version", 1),
                }
                for r in rows
            ]
            await self.client.table(self.TABLE).insert(payload).execute()
            return len(payload)

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO golden_datasets
                    (pipeline_id, organization_id, question, expected_answer,
                     expected_chunks, question_type, set_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                [
                    (
                        r["pipeline_id"],
                        r["organization_id"],
                        r["question"],
                        r.get("expected_answer"),
                        r.get("expected_chunks") or [],
                        r["question_type"],
                        r.get("set_version", 1),
                    )
                    for r in rows
                ],
            )
        return len(rows)
