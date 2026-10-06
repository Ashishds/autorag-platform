"""Evaluation contracts (LLD §6.2, §9.5)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    pipeline_id: UUID
    run_id: UUID | None = None
    adversarial_dynamic_count: int = 5


class RagasScores(BaseModel):
    context_precision: float | None = None
    context_recall: float | None = None
    answer_faithfulness: float | None = None
    answer_relevancy: float | None = None


class EvaluationResult(BaseModel):
    run_id: UUID
    golden_set_id: UUID
    unified_score: float
    retrieval_score: float
    quality_score: float
    faithfulness_score: float
    latency_penalty: float = 0.0
    cost_penalty: float = 0.0
    ragas: RagasScores = Field(default_factory=RagasScores)
    ragas_scorer: str = "gemini-2.5-pro"
    adversarial_pass_rate: float | None = None
    deploy_eligible: bool = False
    diagnosis: list[str] = Field(default_factory=list)
    judge_reasoning: str | None = None
