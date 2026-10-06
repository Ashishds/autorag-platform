"""ApprovalService — 3-tier approval model (LLD §14)."""

from __future__ import annotations

from app.models import ApprovalTier

HIGH_RISK = {"llm_judge", "embedding_model", "prompt_template", "chunking_strategy"}
MED_RISK = {"retrieval_method", "context_window", "reranker_model"}
LOW_BOUNDS = {"top_k": (5, 20), "temperature": (0.0, 1.0)}  # + chunk_size +-20%


class ApprovalService:
    def __init__(self, experiment_repo=None, audit=None):
        self._repo = experiment_repo
        self._audit = audit

    def classify_tier(self, variant: dict, baseline: dict, approval_mode: str = "human_in_loop") -> ApprovalTier:
        if approval_mode == "auto":
            return ApprovalTier.AUTO
        if approval_mode == "mandatory_gate":
            return ApprovalTier.MANDATORY_GATE

        changes = self._diff(variant, baseline)
        if any(k in changes for k in HIGH_RISK):
            return ApprovalTier.MANDATORY_GATE
        if any(k in changes for k in MED_RISK):
            return ApprovalTier.HUMAN_IN_LOOP
        if changes and all(k in LOW_BOUNDS for k in changes):
            return ApprovalTier.AUTO
        return ApprovalTier.HUMAN_IN_LOOP

    @staticmethod
    def _diff(variant: dict, baseline: dict) -> set[str]:
        keys = set(variant) | set(baseline)
        return {k for k in keys if variant.get(k) != baseline.get(k)}
