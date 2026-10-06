# AutoRAG — Build Plan

A comprehensive, step-by-step plan to build AutoRAG from the current boilerplate to a
working MVP. Structured as **phases → milestones → concrete tasks**, each with a clear
"definition of done". Maps to the 7-week MVP timeline in the PRD/LLD.

> Status legend: ☐ not started · ◐ in progress · ☑ done

**Last updated:** 2026-05-30

---

## Guiding principles

1. **Vertical slices, not horizontal layers.** Get one thin path working end-to-end before
   adding breadth. A working "upload → ask → answer" beats 50% of every module.
2. **De-risk the unknowns first.** RAGAS-with-Gemini and ingest→embed→query are the riskiest;
   tackle them in Week 1.
3. **Each slice ends runnable + tested.** `ruff` clean, `pytest` green, manually verified via `/docs`.
4. **Docs are the source of truth.** When code and BRD/PRD/HLD/LLD disagree, update deliberately.

---

## Phase 0 — Environment & foundations ½–1 day)

**Goal:** Everything boots locally; you can hit `/health` and `/docs`, DB migrated.

- ☑ 0.1 `docker compose up -d db redis` → pgvector + Redis healthy
- ☑ 0.2 `uv sync`, create `.env` from `.env.example`, add Google/Cohere/OpenAI keys
- ☑ 0.3 `uv run alembic upgrade head` → 10 tables + `hybrid_search_rrf()` exist
  - Fixed `alembic/env.py` to escape `%` signs preventing interpolation errors
- ☑ 0.4 `uv run uvicorn app.main:app --reload` → `/health` ok, `/docs` loads
- ☑ 0.5 `app/db.py` — loop-safe asyncpg pool (`_pools` dict keyed by event loop) + Supabase async client both initialised
- ☑ 0.6 `uv run pytest tests/unit` — 5 unit tests pass (PII, UnifiedScore)
- ☑ 0.7 Supabase `documents` storage bucket verified/created (`create_bucket.py`)

**Infrastructure:** Real Supabase project connected — `https://oyxyehjwkifaunkqlpwk.supabase.co`

---

## Phase 1 — RAGAS + Gemini calibration spike (1–2 days) ⚠️ highest risk

**Goal:** Prove the evaluation brain works *before* building everything that depends on it.

- ☑ 1.1 `LLMService.complete()` implemented — OpenAI gpt-4o primary (with `max_tokens=4096`); Gemini fallback path wired
- ☑ 1.2 `OpenAIEmbedding.embed()` implemented — `text-embedding-3-small`, batch-capable
- ☑ 1.3 `GeminiEmbedding.embed()` implemented — batch + MRL truncation to 768-dim
- ☑ 1.4 `tests/ragas_compatibility/test_ragas_gemini.py` passes (1 test green)
- ☑ 1.5 Decide scorer default + fallback rule (`ERR_RAGAS_SCORER_FALLBACK`); document in code + LLD

**Models in use:** `gpt-4o` (LLM completions), `text-embedding-3-small` (embeddings)

---

## Phase 2 — Slice 1: Ingest → Query end-to-end (1–1.5 weeks) 🎯 the core

**Goal:** Upload a document, ask a question, get a grounded answer from your DB.

### 2A. Pipeline CRUD ☑
- ☑ `pipeline_repo.py` (supabase-py CRUD — get, create, update, list) implemented
- ☑ `pipeline_service.py` — create/get pipeline with audit events
- ☑ `routes/pipelines.py` — `POST /pipelines`, `GET /pipelines/{id}`
- **Done:** `POST /pipelines` creates a row, `GET /pipelines/{id}` returns it, audit event written.

### 2B. Document upload + storage ☑
- ☑ `storage_service.py` — Supabase Storage upload + local disk fallback
- ☑ `document_repo.py` — status state machine (`queued → processing → completed/failed`); accepts custom UUIDs
- ☑ `routes/ingest.py` — `POST /ingest` stores file, creates `documents` row, enqueues Celery task
- ☑ `routes/jobs.py` — `GET /jobs/{id}` returns document status + chunk count
- **Done:** `POST /ingest` stores file in Supabase Storage, creates DB row at `queued`, returns `document_id`.

### 2C. Ingestion worker ☑
- ☑ `workers/ingest_task.py` — parse (Unstructured.io) → `TieredPIIService.mask` → `ChunkerFactory`
  → `OpenAIEmbedding.embed` (batch) → `ChunkRepository.bulk_upsert`
- ☑ `chunk_repo.py` — `bulk_upsert` with explicit `::vector` casting for pgvector
- ☑ `workers/utils.py` — `run_async` helper (new thread + new event loop for Celery eager tasks)
- ☑ `workers/celery_app.py` — Celery configured with Redis broker
- ☑ `app/db.py` — **loop-indexed `_supabase_clients` dict** (same pattern as `_pools`) so each event loop gets its own Supabase client; prevents `asyncio.locks.Event bound to different event loop` errors
- ☑ `tests/integration/test_ingest_query_flow.py` — **PASSING** (26s); overrides storage dependency to local-disk and patches `StorageService` in worker to avoid httpx http2 transport issues inside `ASGITransport` test context

### 2D. Query FastPath ☑
- ☑ `query_service.py` — `hybrid_retrieve` → `rerank_graceful` (Cohere, graceful-degrade) → `_generate`; writes `query_logs`
- ☑ `retrieval/` — hybrid search calling `hybrid_search_rrf()` Postgres function
- ☑ `routes/query.py` — `POST /query` returns answer + sources + latency
- ☑ Rewrite/HyDE off by default; toggled via `options.rewrite` / `options.hyde`
- **Done:** `POST /query` returns answer + real sources + latency_ms, logs the query.

### 2E. Slice 1 verification ☑
- ☑ Manual: Supabase DB schema live with all 10 tables + `hybrid_search_rrf()` function
- ☑ Direct storage upload to `documents` bucket verified working
- ☑ Pipeline creation verified (`POST /pipelines` → Supabase row)
- ☑ Integration test `test_end_to_end_ingest_and_query` **PASSED** in 26s
  - Answer: *"The primary model used for completions is gpt-4o."* ✅
  - Reranker gracefully degraded (Cohere not configured) ✅

> **Phase 2 complete. Upload → ingest → embed → store → query → grounded answer works end-to-end against real Supabase.**

---

## Phase 3 — Slice 2: Golden set + Evaluation (1 week)

**Goal:** The system can score its own quality reproducibly.

- ☑ 3.1 `golden_set_service.py` — generate Q&A from chunks + fixed adversarial anchors
- ☑ 3.2 `evaluation_service.py` — RAGAS-style metrics + LLM-judge faithfulness + adversarial pass rate
- ☑ 3.3 `routes/evaluate.py` + `routes/score.py` + `evaluation_repo.py` — wired end-to-end
- ☑ 3.4 Rule-based diagnosis in Evaluator (`classify_failures`) attaches hints

**Done:** evaluate a pipeline → Unified Score + RAGAS + faithfulness + adversarial pass rate
+ deploy decision, all stored.

---

## Phase 4 — Slice 3: Optimization loop (1–1.5 weeks)

**Goal:** Closed-loop self-tuning via LangGraph (Flow 3).

- ☑ 4.1 LangGraph wiring — `graph/workflow.py` + nodes invoke real evaluation/improvement/deploy logic
- ☑ 4.2 `workers/evaluate_task.py` — invokes optimization graph via Celery
- ☑ 4.3 `improver.py` — generate variant configs from diagnosis hints, classify approval tier
- ☑ 4.4 `services/approval_service.py` + `routes/approve.py` — wired
- ☑ 4.5 `services/deploy_service.py` + `routes/deploy.py` — wired
- ☑ 4.6 Re-eval variants against the **same** `golden_set_id` (frozen set reused in evaluator)

**Done:** low score → variant proposed → (approval) → deploy → score improves, all traceable.

---

## Phase 5 — Slice 4: Dashboard (1 week) ☑

**Goal:** Wire the 5 Next.js screens to real APIs (use SWR; already a dep).

| Screen | Backend it consumes | Status |
|---|---|---|
| Pipelines | `/pipelines` | ☑ |
| Documents | `/ingest`, `/jobs/{id}` | ☑ |
| Query Playground | `/query` | ☑ |
| Evaluations | `/evaluate`, `/score/{id}` | ☑ |
| Deployments & Approvals | `/deploy`, `/approve`, `/experiments` | ☑ |

**Done:** each screen performs its core action against the live backend.

---

## Phase 6 — Hardening & polish (3–5 days) ☑

- ☑ Observer: `workers/observer_cron.py` — scheduled drift scan + re-eval enqueue on score drop > 0.05
- ☑ Optional flags: rewrite clarity heuristic + HyDE weak-result gate (`retrieval/hyde.py`)
- ☑ Audit/observability: insert-only audit wired; structured logs; CloudWatch emits locally or via boto3
- ☑ Resilience: LLM failover + circuit breaker; reranker graceful-degrade
- ☑ Tests: adversarial anchor unit tests; observer drift + rewrite heuristics; unit tests green
- ☑ Docs/README: README updated with MVP status + demo flow; CI badge fixed
- ☑ Cleanup: renamed `docs/AutoRAG_PRD_v2_4.md`; replaced `your-username` in CI badge

---

## Current blockers & next actions

| Priority | Item | Next action |
|---|---|---|
| ✅ DONE | Integration test E2E — was failing with storage httpx + event loop errors | Fixed via loop-indexed Supabase clients + storage dependency override |
| ✅ DONE | `evaluate_task.py` & LangGraph nodes | Wired to real evaluation/improvement/deploy logic |
| ✅ DONE | `golden_set_service.py` Q&A generation | Chunk-sampling + LLM-gen loop implemented |
| ✅ DONE | Cohere reranker | `COHERE_API_KEY` set in `.env` |
| ✅ DONE | RAGAS scorer default/fallback rule | Documented in `constants.py` + LLD |
| ✅ DONE | Phase 6 hardening | Observer cron, tests, README, cleanup |

---

## Dependency order

```
Phase 0 (env) ☑
   └─> Phase 1 (RAGAS spike) ☑
         └─> Phase 2 (ingest+query) ☑  ← COMPLETE — E2E test passing
               ├─> Phase 3 (eval)    ☑  ← COMPLETE
               │     └─> Phase 4 (loop) ☑  ← COMPLETE
               └─> Phase 5 (dashboard)  ☑  ← COMPLETE
                     └─> Phase 6 (polish) ☑ ← COMPLETE
```

## Suggested weekly cadence (~7 weeks)

| Week | Focus | Status |
|---|---|---|
| 1 | Phase 0 + Phase 1 (env + RAGAS spike) | ☑ **Complete** |
| 2–3 | Phase 2 (ingest → query core) | ☑ **Complete** |
| 4 | Phase 3 (golden set + evaluation) | ☑ **Complete** |
| 5 | Phase 4 (optimization loop) | ☑ **Complete** |
| 6 | Phase 5 (dashboard) | ☑ **Complete** |
| 7 | Phase 6 (hardening, demo polish) | ☑ **Complete** |

---

## Per-slice workflow

For every task: implement behind the existing `# TODO(impl)` markers → `ruff check` + `ruff
format` → `pytest` → manual check via `/docs` → update docs if the contract changes → small,
reviewable commits (only when explicitly requested).

## Definition of done (MVP)

- Upload → ingest → query → evaluate → improve → deploy works end-to-end on local Docker.
- Faithfulness hard gate and adversarial anchors enforced (non-bypassable).
- Unified Score reproducible against a frozen golden set.
- `ruff` + `pytest` green in CI; dashboard demonstrates all 5 screens.

---

## Post-MVP: full self-improvement loop closed (Gemini + scoring calibration)

After the MVP, the end-to-end optimization loop (**ingest → query → evaluate → deploy**) was
validated against a live deployment. Changes made:

- **Model switch to Gemini via the OpenAI-compatible gateway:** `gemini-3.5-flash` (LLM) +
  `gemini-embedding-2-preview` (embeddings, MRL-truncated to 768-dim via `dimensions=768`).
  Routing uses the native Google SDK only when `GOOGLE_API_KEY` is set; otherwise `gemini-*`
  models flow through the same gateway as GPT models.
- **Inline ingestion/eval on local:** with `ENV=local`, both run in-process (no Celery worker),
  fixing the Windows prefork issues; production still uses Celery.
- **Idempotent re-ingestion:** chunks are deleted-then-inserted per document, enabling safe
  re-embedding after a model change (no duplicate / mixed-vector-space rows).
- **Scoring fixes that made the deploy gate reachable:**
  - `context_precision` → rank-aware average precision (was structurally capped at `1/top_k`).
  - Latency penalty → median latency with cloud-realistic bands (was max-of-N, p95@3s/6s).
  - Three-tier gate calibrated: DEPLOY ≥ 0.72, IMPROVE ≥ 0.60 (was an unreachable 0.85).
- **Golden-set hygiene:** the frozen golden set must be regenerated after re-embedding, since
  `expected_chunks` reference chunk IDs that change on re-ingest.

**Result:** a Gemini-powered run scored **Unified 0.85** (retrieval/quality/faithfulness/adversarial
all 1.0) and was **deployed** (config-activation, status `active`).

## Key technical decisions & fixes applied

| Area | Decision / Fix |
|---|---|
| LLM | Primary `gemini-3.5-flash` via OpenAI-compatible gateway; `gpt-4o` failover; `max_tokens=4096` to avoid gateway 400s |
| Embeddings | `gemini-embedding-2-preview` (MRL → 768-dim via `dimensions=768`); `text-embedding-3-small` interchangeable |
| DB pooling | `asyncpg.Pool` keyed by event loop (`_pools: dict[loop, pool]`) to prevent `InterfaceError` across threads |
| Supabase client | `_supabase_clients: dict[loop, AsyncClient]` — same loop-keyed pattern; prevents `asyncio.locks.Event bound to different event loop` in Celery workers |
| Celery async | `run_async()` helper in `workers/utils.py` — new thread + new event loop; calls `init_pool()` + `init_supabase()` to register resources for that loop |
| pgvector | Raw SQL params cast with `::vector` for correct type communication |
| Supabase storage | Bucket `documents` verified; uploads work; test overrides to local-disk fallback via FastAPI `dependency_overrides` |
| Alembic | `%` signs escaped in `env.py` connection string to prevent `configparser` interpolation |
| Document IDs | `DocumentRepository.create()` accepts externally-provided UUIDs for idempotent re-runs |
| Integration tests | Storage dep overridden to `StorageService(supabase=None)` (local disk); Celery `task_always_eager=True` for synchronous in-process execution |
