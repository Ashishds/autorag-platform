"""HyDE re-retrieval — optional flag, only when first-pass results are weak (LLD §12)."""

from __future__ import annotations

from uuid import UUID

from app.constants import HYDE_MIN_STRONG_HITS, HYDE_STRONG_HIT_THRESHOLD
from app.models import ScoredChunk
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding.base import BaseEmbeddingProvider
from app.services.llm.service import LLMService


def is_weak(chunks: list[ScoredChunk]) -> bool:
    strong = [c for c in chunks if (c.score or c.rrf_score) >= HYDE_STRONG_HIT_THRESHOLD]
    return len(strong) < HYDE_MIN_STRONG_HITS


async def maybe_hyde(
    query: str,
    pipeline_id: UUID,
    current_top: list[ScoredChunk],
    chunk_repo: ChunkRepository,
    embedder: BaseEmbeddingProvider,
    llm: LLMService,
) -> list[ScoredChunk]:
    if not is_weak(current_top):
        return current_top  # strong results -> skip HyDE
    hyde_doc = await llm.complete(
        [{"role": "user", "content": f"Write a short passage answering: {query}"}],
        model_preference="gemini-2.5-flash",
    )
    emb = await embedder.embed_one(hyde_doc.content)
    extra = await chunk_repo.hybrid_search(query, emb, pipeline_id, limit=5)
    return _merge_dedup(current_top, extra)[:5]


def _merge_dedup(a: list[ScoredChunk], b: list[ScoredChunk]) -> list[ScoredChunk]:
    seen: set = set()
    out: list[ScoredChunk] = []
    for c in [*a, *b]:
        if c.chunk_id in seen:
            continue
        seen.add(c.chunk_id)
        out.append(c)
    return out
