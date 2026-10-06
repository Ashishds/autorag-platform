"""Internal domain models (not API contracts — those live in app/schemas).

These are lightweight dataclasses passed between services, repositories, and
the LangGraph nodes. API request/response models are Pydantic (app/schemas).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class ChunkStrategy(str, Enum):
    SEMANTIC = "semantic"
    HIERARCHICAL_PARENT = "hierarchical_parent"
    HIERARCHICAL_CHILD = "hierarchical_child"


class DeployDecision(str, Enum):
    DEPLOY = "deploy"
    IMPROVE = "improve"
    BLOCKED_FAITHFULNESS = "blocked_faithfulness"
    BLOCKED_ADVERSARIAL = "blocked_adversarial"
    BLOCKED_SCORE = "blocked_score"


class ApprovalTier(str, Enum):
    AUTO = "auto"
    HUMAN_IN_LOOP = "human_in_loop"
    MANDATORY_GATE = "mandatory_gate"


@dataclass
class Chunk:
    content: str
    chunk_index: int
    token_count: int
    strategy: ChunkStrategy
    page_number: int | None = None
    source_type: str = "text"
    media_path: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class EmbeddedChunk:
    document_id: UUID
    pipeline_id: UUID
    organization_id: UUID
    chunk_index: int
    token_count: int
    content: str
    embedding: list[float]
    strategy: ChunkStrategy
    page_number: int | None = None
    source_type: str = "text"
    media_path: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredChunk:
    chunk_id: UUID
    content: str
    rrf_score: float
    score: float = 0.0  # post-rerank score
    page_number: int | None = None
    document_id: UUID | None = None
    filename: str | None = None
    chunk_index: int | None = None
    source_type: str | None = None
    media_path: str | None = None


@dataclass
class LLMResponse:
    content: str
    provider: str
    reasoning: str | None = None
    token_count: int | None = None


@dataclass
class EvalMetrics:
    retrieval: float
    quality: float
    faithfulness: float
    latency_penalty: float = 0.0
    cost_penalty: float = 0.0


@dataclass
class GoldenQA:
    id: UUID
    question: str
    expected_answer: str | None = None
    expected_chunks: list[UUID] = field(default_factory=list)
    question_type: str = "synthetic"
