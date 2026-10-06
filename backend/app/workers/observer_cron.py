"""Observer cron — scheduled drift scan (MVP Observer is a cron job, not real-time)."""

from __future__ import annotations

import uuid
from uuid import UUID

from app.db import get_pool, get_supabase
from app.logging_config import log
from app.repositories.deployment_repo import DeploymentRepository
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.run_repo import RunRepository
from app.schemas.tasks import EvalTaskPayload
from app.services.observer_service import detect_score_drift
from app.workers.celery_app import celery
from app.workers.evaluate_task import run_evaluation
from app.workers.utils import run_async


@celery.task(name="app.workers.observer_cron.run_observer_scan")
def run_observer_scan() -> dict:
    return run_async(_run_observer_scan())


async def _run_observer_scan() -> dict:
    supabase = None
    try:
        supabase = get_supabase()
    except RuntimeError:
        pass
    pool = get_pool()
    deploy_repo = DeploymentRepository(supabase, pool=pool)
    eval_repo = EvaluationRepository(supabase, pool=pool)
    pipeline_repo = PipelineRepository(supabase, pool=pool)
    run_repo = RunRepository(supabase, pool=pool)

    active = await deploy_repo.list_active()
    drift_triggered = 0

    for dep in active:
        pipeline_id = UUID(str(dep["pipeline_id"]))
        history = await eval_repo.list_scores_for_pipeline(pipeline_id, limit=6)
        if len(history) < 2:
            continue

        latest = float(history[0]["unified_score"])
        prior = [float(r["unified_score"]) for r in history[1:]]
        if not detect_score_drift(latest, prior):
            continue

        pipeline = await pipeline_repo.get(pipeline_id)
        if not pipeline:
            continue

        org_id = pipeline["organization_id"]
        if isinstance(org_id, str):
            org_id = UUID(org_id)

        run_id = uuid.uuid4()
        trace_id = uuid.uuid4()
        await run_repo.create(
            {
                "id": run_id,
                "pipeline_id": pipeline_id,
                "organization_id": org_id,
                "trace_id": trace_id,
                "status": "pending",
                "triggered_by": "observer",
                "metadata": {"drift_trigger": True, "prior_avg": sum(prior) / len(prior)},
            }
        )
        run_evaluation.delay(
            EvalTaskPayload(
                pipeline_id=pipeline_id,
                organization_id=org_id,
                run_id=run_id,
                trace_id=trace_id,
            ).model_dump()
        )
        drift_triggered += 1
        log.info(
            "observer_drift_triggered",
            pipeline_id=str(pipeline_id),
            run_id=str(run_id),
            latest_score=latest,
        )

    log.info("observer_scan_complete", scanned=len(active), drift_triggered=drift_triggered)
    return {"scanned": len(active), "drift_triggered": drift_triggered}
