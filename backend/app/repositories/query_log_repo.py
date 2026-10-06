"""QueryLogRepository (LLD §3.9). asyncpg for high-write-throughput logging."""

from __future__ import annotations

import hashlib

from app.repositories.base import AsyncpgRepository


class QueryLogRepository(AsyncpgRepository):
    async def insert(self, row: dict) -> None:
        q = row.get("q", "")
        query_hash = row.get("query_hash") or hashlib.sha256(q.encode("utf-8")).hexdigest()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO query_logs
                    (pipeline_id, organization_id, trace_id, query_hash,
                     rewrite_applied, hyde_applied, compression_applied,
                     retrieval_k, chunks_retrieved, rerank_applied,
                     latency_ms, token_count, llm_provider)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                row["pipeline_id"],
                row["organization_id"],
                row["trace_id"],
                query_hash,
                row.get("rewrite_applied", False),
                row.get("hyde_applied", False),
                row.get("compression_applied", False),
                row.get("retrieval_k", 5),
                row.get("chunks_retrieved", 0),
                row.get("rerank_applied", False),
                row["latency_ms"],
                row.get("token_count"),
                row.get("llm_provider"),
            )
