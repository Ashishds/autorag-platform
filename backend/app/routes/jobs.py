"""Jobs route — poll background job / document status."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_document_repo, get_pipeline_repo
from app.repositories.document_repo import DocumentRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.schemas.common import APIResponse
from app.schemas.pipeline import ChunkingStrategy
from app.schemas.tasks import IngestTaskPayload
from app.workers.ingest_task import dispatch_ingestion

router = APIRouter()

# "completed" is retryable so documents can be re-embedded (e.g. after an
# embedding-model change); re-ingestion is idempotent (chunks are replaced).
RETRYABLE = {"queued", "failed", "completed"}


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    try:
        doc = await doc_repo.get(job_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Job/Document not found")
        return APIResponse.ok(
            {
                "job_id": job_id,
                "status": doc["status"],
                "chunk_count": doc.get("chunk_count", 0),
                "pii_entities": doc.get("pii_entities", 0),
                "error": doc.get("error"),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_JOB_STATUS_FAILED", str(exc))


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: UUID,
    doc_repo: DocumentRepository = Depends(get_document_repo),
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
):
    try:
        doc = await doc_repo.get(job_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Job/Document not found")

        status = doc["status"]
        if status not in RETRYABLE:
            raise HTTPException(
                status_code=409,
                detail=f"Document status '{status}' cannot be retried",
            )

        pipeline_id = uuid.UUID(str(doc["pipeline_id"]))
        pipeline = await pipeline_repo.get(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        await doc_repo.set_status(job_id, "queued", error=None)

        payload = IngestTaskPayload(
            document_id=job_id,
            pipeline_id=pipeline_id,
            organization_id=uuid.UUID(str(doc["organization_id"])),
            storage_path=doc["storage_path"],
            chunking_strategy=ChunkingStrategy(pipeline["chunking_strategy"]),
            sensitive=False,
        )
        dispatch_ingestion(payload)

        doc = await doc_repo.get(job_id)
        return APIResponse.ok(
            {
                "job_id": job_id,
                "status": doc["status"] if doc else "queued",
                "chunk_count": doc.get("chunk_count", 0) if doc else 0,
                "pii_entities": doc.get("pii_entities", 0) if doc else 0,
                "error": doc.get("error") if doc else None,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_JOB_RETRY_FAILED", str(exc))
