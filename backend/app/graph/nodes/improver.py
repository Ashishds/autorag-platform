"""Improver node — generate variants, classify approval tier, test on the SAME golden set."""

from __future__ import annotations

from app.db import get_pool, get_supabase
from app.graph.state import ApprovalTier, OptimizationState
from app.models import ApprovalTier as ModelApprovalTier
from app.repositories.experiment_repo import ExperimentRepository
from app.services.approval_service import ApprovalService


def _propose_variant(diagnosis: list[str], baseline: dict) -> dict:
    variant = dict(baseline)
    for hint in diagnosis:
        if hint == "increase_top_k_or_chunk_overlap":
            variant["top_k"] = min(int(variant.get("top_k", 5)) + 3, 20)
        elif hint == "enable_rerank_or_tighten_chunks":
            variant["rerank_enabled"] = True
        elif hint == "strengthen_grounding_prompt":
            variant["grounding_strict"] = True
        elif hint == "add_refusal_instruction":
            variant["refusal_instruction"] = True
    if variant == baseline:
        variant["top_k"] = min(int(baseline.get("top_k", 5)) + 2, 20)
    return variant


async def improver_node(state: OptimizationState) -> OptimizationState:
    approval = ApprovalService()
    supabase = None
    try:
        supabase = get_supabase()
    except RuntimeError:
        pass
    exp_repo = ExperimentRepository(supabase, pool=get_pool())

    variant = _propose_variant(state.diagnosis, state.pipeline_config)
    state.variant_configs = [variant] if variant else []

    if variant:
        tier = approval.classify_tier(variant, state.pipeline_config, getattr(state, "approval_mode", "human_in_loop"))
        state.approval_tier = ApprovalTier(tier.value)

        if tier == ModelApprovalTier.AUTO:
            state.approved_variant = variant
            state.pipeline_config = variant
        else:
            await exp_repo.insert(
                {
                    "run_id": state.run_id,
                    "organization_id": state.organization_id,
                    "golden_set_id": state.golden_set_id,
                    "variant_config": variant,
                    "improvement_type": state.diagnosis[0] if state.diagnosis else "general",
                    "approval_tier": tier.value,
                    "approval_status": "pending",
                }
            )

    state.current_agent = "improver"
    return state
