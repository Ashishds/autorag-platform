from __future__ import annotations

import base64
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
    app.dependency_overrides[get_storage_service] = _get_local_storage
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
async def test_image_ingest_query_and_serve_flow(client):
    # 1. Create a pipeline
    pipeline_payload = {
        "name": "Multimodal Test Pipeline",
        "description": "Used to test image parsing and multimodal citations",
        "chunking_strategy": "semantic",
        "retrieval_method": "hybrid",
        "llm_judge": "gpt-4o",
        "approval_mode": "human_in_loop",
        "config": {},
    }

    response = await client.post("/api/v1/pipelines", json=pipeline_payload)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success"
    pipeline_id = res_data["data"]["id"]

    # 2. Upload a dummy 1x1 PNG image
    # A valid base64-encoded 1x1 transparent PNG image
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    png_bytes = base64.b64decode(png_base64)

    files = {"file": ("pixel.png", png_bytes, "image/png")}
    data = {"pipeline_id": pipeline_id, "sensitive": "false"}

    response = await client.post("/api/v1/ingest", data=data, files=files)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success"
    doc_id = res_data["data"]["document_id"]
    assert doc_id is not None

    # 3. Check job status
    response = await client.get(f"/api/v1/jobs/{doc_id}")
    assert response.status_code == 200, response.text
    job_info = response.json()["data"]
    assert job_info["status"] == "completed"
    assert job_info["chunk_count"] == 1

    # 4. Verify file serving route returns the uploaded PNG
    response = await client.get(f"/api/v1/ingest/files/{doc_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == png_bytes

    # 5. Query and verify the image chunk is retrieved
    query_payload = {
        "pipeline_id": pipeline_id,
        "q": "image screenshot pixel description",
        "top_k": 1,
        "mode": "fast",
        "options": {"rewrite": "off", "hyde": "off"},
    }

    response = await client.post("/api/v1/query", json=query_payload)
    assert response.status_code == 200, response.text
    query_result = response.json()["data"]
    
    assert query_result["answer"] != ""
    assert len(query_result["sources"]) == 1
    
    source = query_result["sources"][0]
    assert source["source_type"] == "image"
    assert source["media_path"] is not None
    assert source["document_id"] == doc_id
