"""Abstract embedding provider (LLD §9.2)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Batch embed (used by ingestion)."""
        ...

    @abstractmethod
    async def embed_one(self, text: str) -> list[float]:
        """Single embed (used by query path)."""
        ...

    @abstractmethod
    def dimensions(self) -> int: ...
