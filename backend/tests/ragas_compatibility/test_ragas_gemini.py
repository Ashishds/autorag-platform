"""Week-1 RAGAS + Gemini/Euron calibration test (LLD §18.2).

This test de-risks the single biggest unknown: whether the LLM and Embedding
endpoints (Euron in this case) work correctly when invoked by the services.
"""

import pytest

from app.services.embedding import get_embedding_provider
from app.services.llm.service import LLMService


@pytest.mark.asyncio
async def test_euron_llm_and_embedding_service_work():
    # 1. Test LLM complete
    llm_service = LLMService()
    messages = [{"role": "user", "content": "Say hello in exactly 3 words."}]
    response = await llm_service.complete(messages)
    assert response is not None
    assert response.content != ""
    print(f"\nLLM Response: {response.content}")

    # 2. Test Embedding embed
    embedder = get_embedding_provider()
    embedding = await embedder.embed_one("Hello world")
    assert embedding is not None
    assert len(embedding) == 768
    print(f"\nEmbedding Dimensions: {len(embedding)}")
