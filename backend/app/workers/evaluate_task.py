"""Evaluation Celery task — kicks off the LangGraph optimization loop (Flow 3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.db import init_pool, init_supabase
from app.graph.state import OptimizationState
from app.graph.workflow import build_optimization_graph
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.run_repo import RunRepository
from app.schemas.tasks import EvalTaskPayload
from app.workers.celery_app import celery
from app.workers.utils import run_async


def dispatch_evaluation(payload: EvalTaskPayload) -> dict | None:
    """Run evaluation inline on local dev; enqueue Celery task in production."""
    from app.config import settings

    if settings.ENV == "local":
        return run_async(_run_eval(payload))
    run_evaluation.delay(payload.model_dump())
    return None


@celery.task(name="app.workers.evaluate_task.run_evaluation", bind=True, max_retries=2)
def run_evaluation(self, payload: dict) -> dict:
    parsed = EvalTaskPayload.model_validate(payload)
    return run_async(_run_eval(parsed))


async def _run_eval(payload: EvalTaskPayload) -> dict:
    # Bind pool + Supabase client to the current event loop (the worker thread's
    # loop when run inline) so downstream get_pool()/get_supabase() resolve here.
    pool = await init_pool()
    supabase = await init_supabase()
    run_repo = RunRepository(supabase, pool=pool)
    pipeline_repo = PipelineRepository(supabase, pool=pool)

    await run_repo.update_status(
        payload.run_id, "running", started_at=datetime.now(UTC).isoformat()
    )

    pipeline = await pipeline_repo.get(payload.pipeline_id)
    if not pipeline:
        await run_repo.update_status(payload.run_id, "failed", error_message="Pipeline not found")
        return {"run_id": str(payload.run_id), "status": "failed"}

    config = pipeline.get("config") or {}
    if isinstance(config, str):
        import json

        config = json.loads(config)

    state = OptimizationState(
        run_id=payload.run_id,
        pipeline_id=payload.pipeline_id,
        organization_id=payload.organization_id,
        trace_id=payload.trace_id,
        golden_set_id=uuid.UUID(int=0),
        pipeline_config=config,
        approval_mode=pipeline.get("approval_mode", "human_in_loop"),
    )

    try:
        graph = build_optimization_graph()
        final = await graph.ainvoke(state)
        if isinstance(final, dict):
            diagnosis = final.get("diagnosis", [])
            unified = final.get("unified_score")
        else:
            diagnosis = final.diagnosis
            unified = final.unified_score

        await run_repo.update_status(
            payload.run_id,
            "completed",
            completed_at=datetime.now(UTC).isoformat(),
            metadata={"diagnosis": diagnosis, "unified_score": unified},
        )
        return {
            "run_id": str(payload.run_id),
            "status": "completed",
            "unified_score": unified,
            "diagnosis": diagnosis,
        }
    except Exception as exc:
        await run_repo.update_status(payload.run_id, "failed", error_message=str(exc))
        raise
