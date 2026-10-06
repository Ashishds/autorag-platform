"""Gemini embedding provider with batching + retry (LLD §9.3; Agentset batch pattern)."""

from __future__ import annotations

import asyncio
import math

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.constants import EMBEDDING_BATCH_SIZE, EMBEDDING_MAX_CONCURRENT, EMBEDDING_MAX_RETRIES
from app.exceptions import EmbeddingError
from app.services.embedding.base import BaseEmbeddingProvider

# gemini-embedding-2 default output is 3072-dim; MRL-truncated outputs (<3072)
# must be L2-normalised before use (Google embedding guidance).
_GEMINI_NATIVE_DIM = 3072


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


class GeminiEmbedding(BaseEmbeddingProvider):
    def __init__(self, model: str | None = None, dim: int | None = None):
        self.model = model or settings.EMBEDDING_MODEL
        self._dim = dim or settings.EMBEDDING_DIM

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
            from google import genai  # lazy import
            from google.genai import types

            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            resp = await client.aio.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=self._dim),
            )
            vectors = [list(e.values) for e in resp.embeddings]
            # MRL-truncated outputs (dim < native 3072) require L2 normalisation.
            if self._dim < _GEMINI_NATIVE_DIM:
                vectors = [_l2_normalize(v[: self._dim]) for v in vectors]
            return vectors
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError(f"embedding batch failed: {exc}") from exc
