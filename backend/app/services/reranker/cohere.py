"""Cohere Rerank v3.5 provider. Raises RerankerError so the pipeline can degrade gracefully."""

from __future__ import annotations

from app.config import settings
from app.exceptions import RerankerError
from app.models import ScoredChunk
from app.services.reranker.base import BaseReranker


class CohereReranker(BaseReranker):
    def __init__(self, model: str | None = None):
        self.model = model or settings.RERANKER_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            import cohere  # lazy import
            self._client = cohere.AsyncClientV2(api_key=settings.COHERE_API_KEY)
        return self._client

    async def rerank(self, query: str, chunks: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
        if not chunks:
            return []
        try:
            client = self._get_client()
            resp = await client.rerank(
                model=self.model,
                query=query,
                documents=[c.content for c in chunks],
                top_n=top_k,
            )
            ranked: list[ScoredChunk] = []
            for r in resp.results:
                c = chunks[r.index]
                c.score = r.relevance_score
                ranked.append(c)
            return ranked
        except Exception as exc:  # noqa: BLE001 - normalized; caller degrades gracefully
            raise RerankerError(f"cohere rerank failed: {exc}") from exc

