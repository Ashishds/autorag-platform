"""Abstract reranker (LLD §9.2)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import ScoredChunk


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, chunks: list[ScoredChunk], top_k: int
    ) -> list[ScoredChunk]: ...
