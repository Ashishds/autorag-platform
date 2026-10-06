# AGENTS.md — AutoRAG

Canonical guidance for AI coding agents (Cursor, Claude Code, and others) working in this
repo. Keep this file as the single source of truth; tool-specific files point here.

## What this project is

AutoRAG is an **autonomous RAG optimization platform**. It builds a RAG pipeline from uploaded
documents, scores its own quality against a frozen evaluation set, diagnoses weaknesses,
generates improved configs, and (with approval) deploys the best one — then watches for drift.

The "9-agent" model is **conceptual**. For MVP it is implemented as **~5 components** across
**3 flows**:

1. **Ingest** (Celery): parse → PII mask → chunk → embed → index. *(Builder is folded in here.)*
2. **Query FastPath** (synchronous FastAPI, NOT LangGraph): rewrite\* → hybrid retrieve (DB-level
   RRF) → Cohere rerank → generate.
3. **Optimization Loop** (LangGraph, checkpointed): Evaluator (+ rule-based diagnosis) → Observer
   → Improver → Deployer.

\* `rewrite` and `hyde` are **optional flags, off by default**. **Context Compressor is deferred to
Phase 2** — MVP passes the top-k reranked chunks straight to the LLM.

## Tech stack

- **Backend:** Python 3.12, FastAPI, Celery, LangGraph
- **Data:** Supabase (PostgreSQL + pgvector HNSW + tsvector), Redis 7
- **DB access:** `supabase-py` (CRUD) + `asyncpg` (vector/bulk) + Alembic (raw-SQL). **No ORM.**
- **Models:** Gemini 2.5 Pro/Flash, `gemini-embedding-001` (768-dim), Cohere Rerank v3.5, GPT-4o (failover)
- **Frontend:** Next.js 15
- **Tooling:** `uv`, `ruff`, `pytest`, Docker Compose

## Where things live

```
backend/app/routes/        thin HTTP handlers (no business logic)
backend/app/services/      provider-abstracted LLM/embedding/reranker, PII, evaluation, deploy
backend/app/repositories/  asyncpg (chunk_repo hot path) + supabase-py (CRUD)
backend/app/retrieval/     hybrid, reranker (graceful degrade), hyde
backend/app/chunkers/      semantic, hierarchical
backend/app/graph/         LangGraph optimization loop (Flow 3 ONLY)
backend/app/workers/       Celery: ingest_task, evaluate_task, observer_cron
backend/alembic/           schema + hybrid_search_rrf() PL/pgSQL function
docs/                      BRD, PRD, HLD, LLD — the authoritative spec
```

## Commands

```bash
# infra
docker compose up -d db redis
# backend
cd backend && uv sync && cp .env.example .env && uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run celery -A app.workers.celery_app.celery worker --loglevel=info
uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format
# frontend
cd frontend && npm install && npm run dev
```

## Conventions (see docs/AutoRAG-LLD-v1.0.md §18.3)

- Branches `feature/{slug}` · migrations `{revision}_{description}` · prompts `{name}_v{X}.{Y}.{Z}.j2`
- Python: type-hinted, `ruff`-formatted, line length 100, snake_case functions, PascalCase classes
- API responses use the standard wrapper: `{status, data, error, request_id}`
- Repos: use `asyncpg` for vector search / bulk; `supabase-py` for simple CRUD

## Hard rules (do not violate)

- **Never commit secrets.** Keys go in `.env` (git-ignored); update `.env.example` instead.
- **Faithfulness hard gate** (< 0.50) and **adversarial anchors** (must pass 100%) are
  non-bypassable in deploy decisions. Don't "optimize" them away.
- Keep the **query path synchronous** — do not route Flow 2 through LangGraph.
- Reranker failures must **degrade gracefully** (fall back to RRF order), never hard-fail a query.
- Embeddings are **768-dim**; keep the pgvector column and `hybrid_search_rrf` signature in sync.
- Don't reintroduce Context Compressor or Late Chunking into MVP scope (both are Phase 2).

## Definition of done for a change

1. `ruff check` + `ruff format --check` clean
2. `pytest tests/unit` green
3. New external-facing behavior reflected in the relevant `docs/` file if it changes the spec
4. No secrets, no PII in logs/audit payloads

## Authoritative spec

`docs/` holds the BRD / PRD / HLD / LLD. When code and these docs disagree, the docs win
(or update the docs deliberately as part of the change).
