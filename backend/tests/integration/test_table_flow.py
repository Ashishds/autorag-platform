from __future__ import annotations

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
async def test_table_csv_ingest_and_query_flow(client):
    # 1. Create a pipeline
    pipeline_payload = {
        "name": "Table Test Pipeline",
        "description": "Used to test table row chunking and querying",
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

    # 2. Upload a CSV file containing 12 rows of inventory data (headers + 12 items)
    csv_content = "Product,SKU,Price,Stock\n"
    for i in range(1, 13):
        csv_content += f"Widget {i},SKU-{i:03d},{15.0 + i},{200 + i}\n"

    files = {"file": ("inventory.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {"pipeline_id": pipeline_id, "sensitive": "false"}

    response = await client.post("/api/v1/ingest", data=data, files=files)
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["status"] == "success"
    doc_id = res_data["data"]["document_id"]
    assert doc_id is not None

    # 3. Check job status - 12 rows / group size of 10 should yield 2 chunks
    response = await client.get(f"/api/v1/jobs/{doc_id}")
    assert response.status_code == 200, response.text
    job_info = response.json()["data"]
    assert job_info["status"] == "completed"
    assert job_info["chunk_count"] == 2

    # 4. Query for Widget 11 (which resides in the second chunk group)
    query_payload = {
        "pipeline_id": pipeline_id,
        "q": "Widget 11 price and stock",
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
    assert source["source_type"] == "table"
    assert "Product | SKU | Price | Stock" in source["content"]  # Assert header exists
    assert "Widget 11 |" in source["content"]
    assert "Widget 1 |" not in source["content"]  # Grouped separated
