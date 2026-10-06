"""OptimizationState — the LangGraph state object for Flow 3 (LLD §7.1)."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    retrieval = "retrieval"
    grounding = "grounding"
    context_overflow = "context_overflow"
    refusal = "refusal"
    other = "other"


class ApprovalTier(str, Enum):
    auto = "auto"
    human_in_loop = "human_in_loop"
    mandatory_gate = "mandatory_gate"


class OptimizationState(BaseModel):
    # Identity
    run_id: UUID
    pipeline_id: UUID
    organization_id: UUID
    trace_id: UUID
    golden_set_id: UUID  # constant eval set for this loop

    pipeline_config: dict
    approval_mode: str = "human_in_loop"

    # Evaluation
    unified_score: float | None = None
    retrieval_score: float | None = None
    quality_score: float | None = None
    faithfulness_score: float | None = None
    latency_penalty: float = 0.0
    cost_penalty: float = 0.0
    ragas_scores: dict[str, float] = Field(default_factory=dict)
    ragas_scorer: str = "gemini-2.5-pro"
    adversarial_pass_rate: float | None = None
    deploy_eligible: bool = False
    judge_reasoning: str | None = None

    # Observer / Diagnoser (rule-based inside Evaluator for MVP)
    score_drift_detected: bool = False
    diagnosis: list[str] = Field(default_factory=list)
    failure_type: FailureType | None = None  # populated by LLM Diagnoser in Phase 2
    failure_confidence: float | None = None
    remediation_suggestion: str | None = None

    # Improver
    variant_configs: list[dict] = Field(default_factory=list)
    approval_tier: ApprovalTier | None = None
    approved_variant: dict | None = None

    # Deployer
    deployment_id: UUID | None = None

    # Control
    current_agent: str = "evaluator"
    retry_count: int = 0
    error_message: str | None = None
