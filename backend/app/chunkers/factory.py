"""Chunker routing + factory (LLD §12)."""

from __future__ import annotations

from app.chunkers.base import BaseChunker
from app.chunkers.hierarchical import HierarchicalChunker
from app.chunkers.semantic import SemanticChunker


def route_strategy(strategy: str, doc_hint: str | None = None) -> str:
    """Resolve 'auto' to a concrete strategy. Hierarchical for long/structured docs."""
    if strategy != "auto":
        return strategy
    # TODO(impl): inspect doc structure/length; default to semantic for MVP.
    return "semantic"


class ChunkerFactory:
    def create(self, strategy: str) -> BaseChunker:
        match strategy:
            case "semantic":
                return SemanticChunker()
            case "hierarchical":
                return HierarchicalChunker()
            case _:
                raise ValueError(f"unknown chunking strategy: {strategy}")
