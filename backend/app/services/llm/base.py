"""Abstract LLM provider (LLD §9.2)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import LLMResponse


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        schema: dict | None = None,
    ) -> LLMResponse:
        """Single completion. `schema` requests structured JSON output when provided."""
        ...
