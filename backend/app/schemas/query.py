"""Query FastPath contracts (LLD §6.2). rewrite/hyde are optional flags, default off."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants import DEFAULT_TOP_K


class QueryMode(str, Enum):
    fast = "fast"
    agentic = "agentic"  # optional iterative mode (Phase 2 leaning)


class FlagMode(str, Enum):
    off = "off"
    on = "on"


class QueryOptions(BaseModel):
    rewrite: FlagMode = FlagMode.off
    hyde: FlagMode = FlagMode.off
    multi_query: FlagMode = FlagMode.off
    # NOTE: Context Compressor deferred to Phase 2 — no `compress` option in MVP.


class QueryRequest(BaseModel):
    pipeline_id: UUID
    q: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20)
    mode: QueryMode = QueryMode.fast
    options: QueryOptions = Field(default_factory=QueryOptions)
    metadata_filter: dict | None = None


class Source(BaseModel):
    chunk_id: UUID
    document_id: UUID | None = None
    filename: str | None = None
    chunk_index: int | None = None
    page_number: int | None = None
    score: float
    content: str = ""
    source_type: str | None = None
    media_path: str | None = None


class QueryStages(BaseModel):
    rewrite_applied: bool = False
    hyde_applied: bool = False
    multi_query_applied: bool = False
    agentic_steps: int = 0


class QueryResult(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    latency_ms: int = 0
    llm_provider: str = "gemini-2.5-flash"
    stages: QueryStages = Field(default_factory=QueryStages)
