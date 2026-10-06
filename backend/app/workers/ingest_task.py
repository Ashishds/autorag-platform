"""Ingestion Celery task — Flow 1 (parse -> PII -> chunk -> embed -> index).

Builder is folded in here (single pipeline). Mirrors the LLD IngestionAgent.run().
"""

from __future__ import annotations

from app.schemas.tasks import IngestTaskPayload
from app.workers.celery_app import celery
from app.workers.utils import run_async
import asyncio



def dispatch_ingestion(payload: IngestTaskPayload) -> dict | None:
    """Run ingestion inline on local dev; enqueue Celery task in production."""
    from app.config import settings

    if settings.ENV == "local":
        return run_async(_run_ingestion(payload))
    ingest_document.delay(payload.model_dump())
    return None


@celery.task(name="app.workers.ingest_task.ingest_document", bind=True, max_retries=3)
def ingest_document(self, payload: dict) -> dict:
    parsed = IngestTaskPayload.model_validate(payload)
    return run_async(_run_ingestion(parsed))


async def _run_ingestion(payload: IngestTaskPayload) -> dict:
    import uuid

    from app.chunkers.factory import ChunkerFactory, route_strategy
    from app.db import init_pool, init_supabase
    from app.models import EmbeddedChunk
    from app.repositories.audit_repo import AuditRepository
    from app.repositories.chunk_repo import ChunkRepository
    from app.repositories.document_repo import DocumentRepository
    from app.services.audit_service import AuditService
    from app.services.embedding import get_embedding_provider
    from app.services.llm.service import LLMService
    from app.services.pii.service import TieredPIIService
    from app.services.storage_service import StorageService

    pool = await init_pool()
    supabase_client = await init_supabase()  # creates a fresh client for this event loop

    doc_repo = DocumentRepository(supabase_client, pool=pool)
    chunk_repo = ChunkRepository(pool)
    storage_svc = StorageService(supabase_client)
    llm_svc = LLMService()
    pii_svc = TieredPIIService(llm_svc)
    audit_repo = AuditRepository(supabase_client, pool=pool)
    audit_svc = AuditService(audit_repo)
    chunker_factory = ChunkerFactory()

    doc_id = payload.document_id
    org_id = payload.organization_id
    pipeline_id = payload.pipeline_id

    try:
        # 1. Update status to pre_processing
        await doc_repo.set_status(doc_id, "pre_processing")

        # 2. Download file content
        file_bytes = await storage_svc.download(payload.storage_path)

        # 3. Parse file via ParserRegistry (PDF, DOCX, PPTX, CSV, images, etc.)
        filename = payload.storage_path.split("/")[-1]
        doc_meta = await doc_repo.get(doc_id)
        mime_type = doc_meta.get("mime_type") if doc_meta else None

        from app.parsers.registry import ParserRegistry
        from app.utils.text_normalize import normalize_extracted_text

        registry = ParserRegistry()
        parser = registry.get_parser(filename, mime_type)
        blocks = await parser.parse(
            file_bytes, filename, mime_type, storage_path=payload.storage_path
        )

        # 4. Transition to processing
        await doc_repo.set_status(doc_id, "processing")

        # 5. Run PII masking block-by-block concurrently with bounded semaphore
        from app.parsers.base import DocumentBlock
        masked_blocks = []
        pii_count = 0
        
        sem = asyncio.Semaphore(5)
        
        async def mask_block(b):
            async with sem:
                if b.content and b.content.strip():
                    masked_content, block_pii = await pii_svc.mask(
                        b.content, sensitive=payload.sensitive
                    )
                    return DocumentBlock(
                        type=b.type,
                        content=masked_content,
                        page_number=b.page_number,
                        media_path=b.media_path,
                        metadata=b.metadata,
                    ), block_pii
                return b, 0
                
        results = await asyncio.gather(*(mask_block(b) for b in blocks))
        for mb, p_count in results:
            if mb.content and mb.content.strip():
                masked_blocks.append(mb)
                pii_count += p_count

        if not masked_blocks:
            raise ValueError("No extractable text found in document.")

        # 6. Route and create chunker strategy
        strategy = route_strategy(payload.chunking_strategy.value)
        chunker = chunker_factory.create(strategy)
        chunks = chunker.chunk(masked_blocks)

        if not chunks:
            raise ValueError("Document yielded 0 chunks after splitting.")

        # 7. Generate embeddings
        embedder = get_embedding_provider()
        chunk_texts = [c.content for c in chunks]
        embeddings = await embedder.embed(chunk_texts)

        # 8. Construct EmbeddedChunk models
        embedded_chunks = []
        for i, c in enumerate(chunks):
            embedded_chunks.append(
                EmbeddedChunk(
                    document_id=doc_id,
                    pipeline_id=pipeline_id,
                    organization_id=org_id,
                    chunk_index=c.chunk_index,
                    token_count=c.token_count,
                    content=c.content,
                    embedding=embeddings[i],
                    strategy=c.strategy,
                    page_number=c.page_number,
                    source_type=c.source_type,
                    media_path=c.media_path,
                    metadata=c.metadata,
                )
            )

        # 9. Save chunk embeddings to DB (delete-then-insert => idempotent re-ingest)
        await chunk_repo.delete_for_document(doc_id)
        await chunk_repo.bulk_upsert(embedded_chunks)

        # 10. Update status to completed and set metadata counts
        await doc_repo.set_status(
            document_id=doc_id,
            status="completed",
            chunk_count=len(embedded_chunks),
            pii_entities=pii_count,
        )

        # 11. Write INGESTION_COMPLETED audit event
        await audit_svc.log(
            organization_id=org_id,
            event_type="INGESTION_COMPLETED",
            actor_id=uuid.UUID(int=0),
            resource_type="document",
            resource_id=doc_id,
            trace_id=uuid.uuid4(),
            payload={"chunks": len(embedded_chunks), "pii_entities": pii_count},
        )

        return {"document_id": str(doc_id), "status": "completed", "chunks": len(embedded_chunks)}

    except Exception as exc:
        error_msg = str(exc)
        await doc_repo.set_status(doc_id, "failed", error=error_msg)
        return {"document_id": str(doc_id), "status": "failed", "error": error_msg}
