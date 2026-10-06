"""Pipeline config contracts (LLD §6.2 — direct config, no wizard)."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    semantic = "semantic"
    hierarchical = "hierarchical"
    auto = "auto"


class RetrievalMethod(str, Enum):
    dense = "dense"
    hybrid = "hybrid"
    hybrid_hyde = "hybrid_hyde"


class ApprovalMode(str, Enum):
    auto = "auto"
    human_in_loop = "human_in_loop"
    mandatory_gate = "mandatory_gate"


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.auto
    retrieval_method: RetrievalMethod = RetrievalMethod.hybrid
    llm_judge: str = "gemini-2.5-pro"
    approval_mode: ApprovalMode = ApprovalMode.human_in_loop
    config: dict = Field(default_factory=dict)


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    chunking_strategy: ChunkingStrategy | None = None
    retrieval_method: RetrievalMethod | None = None
    llm_judge: str | None = None
    approval_mode: ApprovalMode | None = None
    config: dict | None = None


class PipelineOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    chunking_strategy: str
    retrieval_method: str
    llm_judge: str
    approval_mode: str
    status: str
    active_version: UUID | None = None
