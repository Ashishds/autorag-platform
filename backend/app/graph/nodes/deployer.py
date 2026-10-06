"""Deployer node — config activation + cache invalidation (LLD §15)."""

from __future__ import annotations

from app.db import get_pool, get_supabase
from app.graph.state import OptimizationState
from app.repositories.deployment_repo import DeploymentRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.services.deploy_service import DeployService


async def deployer_node(state: OptimizationState) -> OptimizationState:
    supabase = None
    try:
        supabase = get_supabase()
    except RuntimeError:
        pass
    pool = get_pool()
    deploy_svc = DeployService(
        deployment_repo=DeploymentRepository(supabase, pool=pool),
        pipeline_repo=PipelineRepository(supabase, pool=pool),
    )

    config = state.approved_variant or state.pipeline_config
    dep = await deploy_svc.activate(
        pipeline_id=state.pipeline_id,
        run_id=state.run_id,
        organization_id=state.organization_id,
        config=config,
        unified_score=state.unified_score or 0.0,
    )
    state.deployment_id = dep["id"]
    state.current_agent = "deployer"
    return state
