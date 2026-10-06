"""End-to-end integration test: ingest → chunk → embed → query.

Strategy
--------
* Real Supabase DB (asyncpg pool + postgrest) for pipelines, documents, chunks, query_logs.
* Storage is overridden to use local-disk fallback — avoids the httpx http2 transport
  incompatibility between storage3's AsyncClient and pytest-asyncio's ASGITransport context.
* Celery runs in-process via task_always_eager=True.
* The ingest worker's StorageService is patched to also use local-disk (no Supabase http calls).
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_storage_service
from app.main import app
from app.services.storage_service import StorageService
from app.workers.celery_app import celery

# Force Celery to execute tasks synchronously inline for integration testing
celery.conf.task_always_eager = True

# Local-disk StorageService — no Supabase httpx calls during tests
_local_storage = StorageService(supabase=None)


def _get_local_storage() -> StorageService:
    return _local_storage


@pytest.fixture
async def client():
    """
    Test HTTP client with:
    - FastAPI dependency override: storage → local disk
    - Worker-level patch: StorageService in ingest_task → local disk
    """
    app.dependency_overrides[get_storage_service] = _get_local_storage
    # Patch StorageService at the source so the lazy import inside _run_ingestion
    # gets the local-disk version (avoids real Supabase http2 transport in tests)
    with patch(
        "app.services.storage_service.StorageService",
        return_value=_local_storage,
    ):
        try:
            async with app.router.lifespan_context(app):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as c:
                    yield c
        finally:
            app.dependency_overrides.pop(get_storage_service, None)


@pytest.mark.asyncio
async def test_end_to_end_ingest_and_query(client):
    # 1. Create a pipeline
    pipeline_payload = {
        "name": "Test Integration Pipeline",
        "description": "Used to test document ingestion and querying end-to-end",
        "chunking_strategy": "semantic",
        "retrieval_method": "hybrid",
        "llm_judge": "gpt-4o",
        "approval_mode": "human_in_loop",
        "config": {},
    }

    response = await client.post("/api/v1/pipelines", json=pipeline_payload)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success", res_data
    pipeline = res_data["data"]
    pipeline_id = pipeline["id"]
    assert pipeline_id is not None

    # 2. Upload a document
    document_content = (
        "AutoRAG is an autonomous Retrieval-Augmented Generation optimization platform.\n\n"
        "It uses a closed-loop optimization system to self-correct and self-tune parameters.\n\n"
        "The primary model used for completions is gpt-4o."
    )

    files = {"file": ("test_doc.txt", document_content.encode("utf-8"), "text/plain")}
    data = {"pipeline_id": pipeline_id, "sensitive": "false"}

    response = await client.post("/api/v1/ingest", data=data, files=files)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success", res_data
    doc_info = res_data["data"]
    doc_id = doc_info["document_id"]
    assert doc_id is not None

    # 3. Check job status
    # task_always_eager=True means Celery ran synchronously above → status should be "completed"
    response = await client.get(f"/api/v1/jobs/{doc_id}")
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success", res_data
    job_info = res_data["data"]
    assert job_info["status"] == "completed", job_info
    assert job_info["chunk_count"] > 0
    assert job_info["error"] is None

    # 4. Query the document
    query_payload = {
        "pipeline_id": pipeline_id,
        "q": "What is the primary model used for completions?",
        "top_k": 3,
        "mode": "fast",
        "options": {"rewrite": "off", "hyde": "off"},
    }

    response = await client.post("/api/v1/query", json=query_payload)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success", res_data
    query_result = res_data["data"]

    assert query_result["answer"] != ""
    assert len(query_result["sources"]) > 0
    assert query_result["latency_ms"] > 0
    print(f"\nIntegration Query Answer: {query_result['answer']}")
