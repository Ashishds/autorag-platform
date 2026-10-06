"""Rerank with graceful degradation (LLD §12; Agentset graceful-degrade pattern)."""

from __future__ import annotations

from app.exceptions import RerankerError
from app.logging_config import log
from app.models import ScoredChunk
from app.services.reranker.base import BaseReranker


async def rerank_graceful(
    query: str,
    chunks: list[ScoredChunk],
    reranker: BaseReranker,
    top_k: int,
) -> list[ScoredChunk]:
    """Rerank; on failure, fall back to the top-k RRF order (no hard failure)."""
    try:
        return await reranker.rerank(query, chunks, top_k)
    except RerankerError:
        log.warning("rerank_failed_degrading", top_k=top_k)
        return chunks[:top_k]
