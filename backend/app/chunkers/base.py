"""Abstract chunker. Two MVP strategies: semantic, hierarchical (late -> Phase 2)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Chunk


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]: ...
