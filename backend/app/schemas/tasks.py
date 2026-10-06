"""Validated Celery task payloads (LLD §10 — Pydantic, like Agentset's Zod payloads)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.pipeline import ChunkingStrategy


class IngestTaskPayload(BaseModel):
    document_id: UUID
    pipeline_id: UUID
    organization_id: UUID
    storage_path: str
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.auto
    sensitive: bool = False


class EvalTaskPayload(BaseModel):
    pipeline_id: UUID
    organization_id: UUID
    run_id: UUID
    trace_id: UUID
    adversarial_dynamic_count: int = 5
