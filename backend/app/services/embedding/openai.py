"""OpenAI-compatible embedding provider with batching + retry (for Euron / OpenAI)."""

from __future__ import annotations

import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.constants import EMBEDDING_BATCH_SIZE, EMBEDDING_MAX_CONCURRENT, EMBEDDING_MAX_RETRIES
from app.exceptions import EmbeddingError
from app.services.embedding.base import BaseEmbeddingProvider


class OpenAIEmbedding(BaseEmbeddingProvider):
    def __init__(self, model: str | None = None, dim: int | None = None):
        self.model = model or settings.EMBEDDING_MODEL
        self._dim = dim or settings.EMBEDDING_DIM
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI  # lazy import
            kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    def dimensions(self) -> int:
        return self._dim

    async def embed_one(self, text: str) -> list[float]:
        out = await self.embed([text])
        return out[0]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed in batches of EMBEDDING_BATCH_SIZE with bounded concurrency."""
        batches = [
            texts[i : i + EMBEDDING_BATCH_SIZE] for i in range(0, len(texts), EMBEDDING_BATCH_SIZE)
        ]
        sem = asyncio.Semaphore(EMBEDDING_MAX_CONCURRENT)

        async def run_batch(batch: list[str]) -> list[list[float]]:
            async with sem:
                return await self._embed_batch(batch)

        results = await asyncio.gather(*(run_batch(b) for b in batches))
        return [vec for batch in results for vec in batch]

    @retry(
        stop=stop_after_attempt(EMBEDDING_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            client = self._get_client()

            # OpenAI embeddings support dimensions option for text-embedding-3 models
            create_kwargs: dict = {
                "model": self.model,
                "input": batch,
            }
            # MRL truncation: OpenAI text-embedding-3 and Gemini Embedding 2
            # both honour an explicit output dimension via the gateway.
            if "text-embedding-3" in self.model or "gemini-embedding" in self.model:
                create_kwargs["dimensions"] = self._dim

            create_kwargs["timeout"] = 30.0
            resp = await client.embeddings.create(**create_kwargs)

            # Extract and ensure correct dimension
            embeddings = []
            for e in resp.data:
                vec = e.embedding
                if len(vec) > self._dim:
                    vec = vec[: self._dim]
                elif len(vec) < self._dim:
                    vec = vec + [0.0] * (self._dim - len(vec))
                embeddings.append(vec)
            return embeddings
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError(f"embedding batch failed: {exc}") from exc

