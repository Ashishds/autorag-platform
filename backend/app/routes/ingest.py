"""Ingestion route — uploads a document, enqueues the ingest Celery job, and serves files."""

from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import (
    get_audit_service,
    get_document_repo,
    get_pipeline_repo,
    get_storage_service,
)
from app.repositories.document_repo import DocumentRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.schemas.common import APIResponse
from app.schemas.tasks import IngestTaskPayload
from app.services.audit_service import AuditService
from app.services.storage_service import StorageService
from app.workers.ingest_task import dispatch_ingestion
def extract_youtube_video_id(url: str) -> str | None:
    import re
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\s]+)',
        r'(?:https?://)?youtu\.be/([^?\s]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?\s]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^?\s]+)',
        r'(?:https?://)?m\.youtube\.com/watch\?v=([^&\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


router = APIRouter()


class URLIngestRequest(BaseModel):
    url: str = Field(min_length=1)
    pipeline_id: uuid.UUID
    sensitive: bool = False


@router.post("/url")
async def ingest_url(
    req: URLIngestRequest,
    storage_svc: StorageService = Depends(get_storage_service),
    doc_repo: DocumentRepository = Depends(get_document_repo),
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
    audit_svc: AuditService = Depends(get_audit_service),
):
    try:
        # 1. Verify pipeline exists and get organization_id
        pipeline = await pipeline_repo.get(req.pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        organization_id = pipeline["organization_id"]
        document_id = uuid.uuid4()

        # 2. Check if YouTube video URL
        video_id = extract_youtube_video_id(req.url)
        if video_id:
            from youtube_transcript_api import YouTubeTranscriptApi
            try:
                fetched = YouTubeTranscriptApi().fetch(video_id)
                transcript = [
                    {"text": s.text, "start": s.start, "duration": s.duration}
                    for s in fetched.snippets
                ]
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not retrieve transcript for YouTube video {video_id}: {e}"
                )
            import json
            content = json.dumps(transcript).encode("utf-8")
            filename = f"youtube_{video_id}.youtube"
            mime_type = "application/x-youtube"
        else:
            # Standard URL
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(req.url, follow_redirects=True)
                resp.raise_for_status()
                content = resp.content

            # Clean/normalize filename from URLnetloc + path
            from urllib.parse import urlparse
            parsed_url = urlparse(req.url)
            clean_path = parsed_url.path.strip("/").replace("/", "_")
            filename = parsed_url.netloc + ("_" + clean_path if clean_path else "")
            if not filename.endswith(".html"):
                filename += ".html"
            mime_type = "text/html"

        # 3. Upload file content to storage
        storage_path = f"{organization_id}/{document_id}/{filename}"
        await storage_svc.upload(
            storage_path, content, mime_type
        )

        # 4. Create document registry row
        doc_row = {
            "id": document_id,
            "organization_id": organization_id,
            "pipeline_id": req.pipeline_id,
            "filename": filename,
            "file_size": len(content),
            "storage_path": storage_path,
            "status": "queued",
            "mime_type": mime_type,
        }
        await doc_repo.create(doc_row)

        # 5. Construct Celery task payload
        payload = IngestTaskPayload(
            document_id=document_id,
            pipeline_id=req.pipeline_id,
            organization_id=organization_id,
            storage_path=storage_path,
            chunking_strategy=pipeline["chunking_strategy"],
            sensitive=req.sensitive,
        )

        # 6. Run Ingestion (Celery task dispatch)
        dispatch_ingestion(payload)

        # 7. Audit log ingestion started
        await audit_svc.log(
            organization_id=organization_id,
            event_type="INGESTION_STARTED",
            actor_id=uuid.UUID(int=0),
            resource_type="document",
            resource_id=document_id,
            trace_id=uuid.uuid4(),
            payload={"filename": filename, "url": req.url},
        )

        return APIResponse.ok(
            {
                "document_id": document_id,
                "status": "queued",
                "storage_path": storage_path,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_INGEST_URL_FAILED", str(exc))


def _document_out(doc: dict) -> dict:
    created = doc.get("created_at")
    return {
        "id": str(doc["id"]),
        "filename": doc["filename"],
        "file_size": doc["file_size"],
        "status": doc["status"],
        "chunk_count": doc.get("chunk_count", 0),
        "error": doc.get("error"),
        "mime_type": doc.get("mime_type"),
        "created_at": str(created) if created is not None else None,
    }


@router.get("/documents")
async def list_documents(
    pipeline_id: uuid.UUID,
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    try:
        rows = await doc_repo.list_by_pipeline(pipeline_id)
        return APIResponse.ok([_document_out(r) for r in rows])
    except Exception as exc:
        return APIResponse.fail("ERR_DOCUMENT_LIST_FAILED", str(exc))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    doc_repo: DocumentRepository = Depends(get_document_repo),
    storage_svc: StorageService = Depends(get_storage_service),
):
    try:
        doc = await doc_repo.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        storage_path = doc.get("storage_path")
        if storage_path:
            try:
                await storage_svc.delete(storage_path)
            except Exception:
                pass  # best-effort storage cleanup

        deleted = await doc_repo.delete(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        return APIResponse.ok({"id": str(document_id), "deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_DOCUMENT_DELETE_FAILED", str(exc))


@router.post("")
async def ingest(
    file: UploadFile = File(...),
    pipeline_id: uuid.UUID = Form(...),
    sensitive: bool = Form(default=False),
    storage_svc: StorageService = Depends(get_storage_service),
    doc_repo: DocumentRepository = Depends(get_document_repo),
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
    audit_svc: AuditService = Depends(get_audit_service),
):
    try:
        # 1. Verify pipeline exists and get its organization_id
        pipeline = await pipeline_repo.get(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        organization_id = pipeline["organization_id"]
        document_id = uuid.uuid4()

        # 2. Upload file content to storage
        content = await file.read()
        storage_path = f"{organization_id}/{document_id}/{file.filename}"
        mime_type = file.content_type or "application/octet-stream"
        await storage_svc.upload(
            storage_path, content, mime_type
        )

        # 3. Create document registry row
        doc_row = {
            "id": document_id,
            "organization_id": organization_id,
            "pipeline_id": pipeline_id,
            "filename": file.filename,
            "file_size": len(content),
            "storage_path": storage_path,
            "status": "queued",
            "mime_type": mime_type,
        }
        await doc_repo.create(doc_row)

        # 4. Construct Celery task payload
        payload = IngestTaskPayload(
            document_id=document_id,
            pipeline_id=pipeline_id,
            organization_id=organization_id,
            storage_path=storage_path,
            chunking_strategy=pipeline["chunking_strategy"],
            sensitive=sensitive,
        )

        # 5. Run ingestion (inline on local dev; Celery worker in production)
        dispatch_ingestion(payload)

        doc = await doc_repo.get(document_id)
        status = doc["status"] if doc else "queued"

        # 6. Audit log ingestion started event
        await audit_svc.log(
            organization_id=organization_id,
            event_type="INGESTION_STARTED",
            actor_id=uuid.UUID(int=0),
            resource_type="document",
            resource_id=document_id,
            trace_id=uuid.uuid4(),
            payload={"filename": file.filename},
        )

        return APIResponse.ok(
            {
                "document_id": document_id,
                "status": status,
                "storage_path": storage_path,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return APIResponse.fail("ERR_INGEST_FAILED", str(exc))


@router.get("/files/{document_id}")
async def get_document_file(
    document_id: uuid.UUID,
    doc_repo: DocumentRepository = Depends(get_document_repo),
    storage_svc: StorageService = Depends(get_storage_service),
):
    """Retrieve raw file from storage and stream it back to the client."""
    doc = await doc_repo.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        file_bytes = await storage_svc.download(doc["storage_path"])
        mime_type = doc.get("mime_type") or "application/octet-stream"
        return StreamingResponse(io.BytesIO(file_bytes), media_type=mime_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {exc}") from exc
