"""FastAPI application entrypoint (LLD §18.2).

Hosts the synchronous Query FastPath and the management/optimization REST API.
The LangGraph optimization loop runs in Celery workers, not in the request path.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings
from app.db import close_pool, close_supabase, init_pool, init_supabase
from app.exceptions import AutoRAGException
from app.logging_config import configure_logging, log
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    try:
        await init_pool()
        log.info("startup_complete", env=settings.ENV)
    except Exception as exc:  # noqa: BLE001 - allow boot without DB for docs/dev
        log.warning("db_pool_unavailable", error=str(exc))
    try:
        await init_supabase()
        log.info("supabase_client_ready")
    except Exception as exc:
        log.warning("supabase_client_unavailable", error=str(exc))
    yield
    await close_supabase(all_loops=True)
    await close_pool(all_loops=True)


app = FastAPI(
    title="AutoRAG API",
    version=__version__,
    description="Autonomous RAG optimization platform (MVP).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AutoRAGException)
async def autorag_exception_handler(request: Request, exc: AutoRAGException):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "data": None,
            "error": {"code": exc.code, "message": exc.message, "details": exc.details},
        },
    )


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": __version__}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
