from app.services.embedding.base import BaseEmbeddingProvider
from app.services.embedding.gemini import GeminiEmbedding
from app.services.embedding.openai import OpenAIEmbedding

__all__ = ["BaseEmbeddingProvider", "GeminiEmbedding", "OpenAIEmbedding", "get_embedding_provider"]


def get_embedding_provider(
    model: str | None = None, dim: int | None = None
) -> BaseEmbeddingProvider:
    from app.config import settings

    target_model = model or settings.EMBEDDING_MODEL
    # Native Gemini SDK only when a Google API key is set; otherwise route
    # gemini-* embedding models through the OpenAI-compatible gateway (Euron).
    if target_model.startswith("gemini") and settings.GOOGLE_API_KEY:
        return GeminiEmbedding(target_model, dim)
    else:
        return OpenAIEmbedding(target_model, dim)
