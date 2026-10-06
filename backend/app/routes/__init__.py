"""Thin route handlers (LLD §18.2). All business logic lives in services."""

from fastapi import APIRouter

from app.routes import (
    approve,
    audit_log,
    deploy,
    diagnose,
    evaluate,
    experiments,
    improve,
    ingest,
    jobs,
    pipelines,
    query,
    runs,
    score,
    connectors,
    oauth,
)

api_router = APIRouter()
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(evaluate.router, prefix="/evaluate", tags=["evaluate"])
api_router.include_router(score.router, prefix="/score", tags=["evaluate"])
api_router.include_router(diagnose.router, prefix="/diagnose", tags=["optimize"])
api_router.include_router(improve.router, prefix="/improve", tags=["optimize"])
api_router.include_router(approve.router, prefix="/approve", tags=["optimize"])
api_router.include_router(deploy.router, prefix="/deploy", tags=["deploy"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["optimize"])
api_router.include_router(audit_log.router, prefix="/audit-log", tags=["audit"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(runs.router, prefix="/runs", tags=["evaluate"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
