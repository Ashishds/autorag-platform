"""Hybrid retrieval — thin wrapper over the DB-level hybrid_search_rrf (LLD §4.2, §12)."""

from __future__ import annotations

from uuid import UUID

from app.constants import HYBRID_CANDIDATE_LIMIT
from app.models import ScoredChunk
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding.base import BaseEmbeddingProvider


async def hybrid_retrieve(
    query: str,
    pipeline_id: UUID,
    chunk_repo: ChunkRepository,
    embedder: BaseEmbeddingProvider,
    limit: int = HYBRID_CANDIDATE_LIMIT,
    metadata_filter: dict | None = None,
) -> list[ScoredChunk]:
    query_emb = await embedder.embed_one(query)
    return await chunk_repo.hybrid_search(
        query, query_emb, pipeline_id, limit=limit, metadata_filter=metadata_filter
    )
