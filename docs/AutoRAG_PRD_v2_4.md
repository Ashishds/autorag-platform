# AutoRAG Platform — Product Requirements Document (PRD)

**Version**: 3.0 (MVP-Hardened Revision) | **Classification**: Proprietary & Confidential
**Project**: AutoRAG Architect
**Date**: May 2026 | **Status**: Approved
**Supersedes**: PRD v2.4

---

# Table of Contents

01. Executive Summary
02. Problem Statement & Why Now
03. Market & Capability Realization
04. Target Users & Personas
05. Product Goals & Success Metrics
06. Scope Definition
07. Solution Architecture — 9-Agent Model, 3 Execution Flows
08. Feature Specifications
09. API & Integration Requirements
10. Data & Storage Design
11. Non-Functional Requirements
12. AI Safety & Governance
13. Monitoring, Observability & LLMOps
14. Testing Strategy
15. UX & UI Requirements
16. Deployment & DevOps
17. Timeline & Milestones — 7-Week Plan
18. Business Model, Pricing & ROI
19. Go-To-Market Strategy
20. Risks & Architectural Guidelines
21. Engineering Operations
22. Sign-Off

---

# 01   Executive Summary

AutoRAG is an enterprise-grade, closed-loop autonomous AI platform that builds, evaluates, observes, diagnoses, and continuously improves Retrieval-Augmented Generation (RAG) pipelines without manual tuning or labeled datasets.

The platform is conceptually a **9-agent system**, implemented pragmatically as **three execution flows**: a background **Ingest flow**, a synchronous **Query FastPath**, and a stateful LangGraph **Optimization loop**. A weighted **Unified Score** is the automated promotion gate. No pipeline configuration is promoted without passing strict quality thresholds.

**Differentiator:** AutoRAG is a **RAG quality-optimization engine**, not a RAG hosting runtime. Its value is the evaluation + self-improvement layer (Unified Score, RAGAS, adversarial testing, diagnose→improve loop).

## 1.1  Platform Delivery Phases

| Phase | Target Date | Definition of Done |
| --- | --- | --- |
| Phase 1 — Core Release (MVP) | 26 June 2026 | 3-flow system active; Unified Score ≥ 0.80 on golden set; core REST API; single ECS service deployed; 5-screen dashboard |
| Phase 2 — Enterprise Scale | Sept 2026 | Multi-model support; SSO + RBAC; Late Chunking; Blue/Green ECS canary; real-time Observer; agentic query mode GA |
| Phase 3 — Managed Cloud | Dec 2026 | Multi-tenant SaaS; managed workspace isolation; SLA monitoring; usage billing |

---

# 02   Problem Statement & Why Now

Tuning a production-quality RAG system is manual and iterative across separate layers (chunking, embedding, retrieval, prompts, generation) with no automated feedback. Teams spend days per iteration. When performance degrades in production, there is usually no automated regression detection or safe rollback.

## 2.1  Key Operational Challenges

| Operational Challenge | Industry Reality | Enterprise Impact |
| --- | --- | --- |
| Multi-Layer Manual Tuning | Parameter tuning is disconnected across stages | Delayed launches; high cost |
| Lack of Standardized Scoring | Quality judged on ad-hoc sample queries | Inconsistent quality; no release bar |
| Disconnected Ingestion & Evaluation | Eval scripts run manually | Slow velocity |
| Undetected Hallucinations | Pipelines ship without verification | Trust damage; costly fixes |
| Manual rollbacks | Recovery needs hotfixes | Downtime |

## 2.2  Technological Enablers

- **Cost Efficiency**: LLM API costs have fallen; high-volume eval is viable — *especially when the eval set is generated once and reused*.
- **Agentic State Machines**: LangGraph enables resilient stateful workflows with checkpointing — used here **only for the asynchronous optimization loop**.
- **Unified Databases**: Supabase merges relational tables, pgvector, storage, and auth into one engine.

---

# 03   Market & Capability Realization

## 3.1  Market Sizing

| Segment | 2024 | 2030 Projection | CAGR |
| --- | --- | --- | --- |
| RAG Infrastructure & LLM Evaluation Tooling | $1.2B | $12B | 47% |
| Enterprise AI Quality & Observability | $0.8B | $6.5B | 42% |
| Low-Code AI Automation | $28B | $187B | 31% |

## 3.2  Platform Capability & Value Matrix

| Architectural Pillar | Core Implementation | Business Value |
| --- | --- | --- |
| **Ingestion & Parsing** | Unstructured.io + **tiered PII masking** | Clean, secure ingestion |
| **Chunking** | **Semantic + Hierarchical** (Late Chunking → Phase 2) | Structure-aware chunking that actually works with the embedding API |
| **Hybrid Retrieval** | pgvector + tsvector via **DB-level RRF** + Cohere Rerank (+ conditional HyDE) | Precise, low-latency retrieval |
| **Execution** | 9-agent model as **3 flows** (ingest job, query FastPath, LangGraph optimize loop) | Fast queries + robust async optimization |
| **Evaluations** | RAGAS + Gemini Judge + Adversarial against a **static stored set** | Reproducible, strict quality gate |
| **Closed-Loop Tuning** | Diagnoser classification + Improver variants tested on the constant set | Auto-tuning with valid comparisons |
| **Observability** | CloudWatch logs/metrics/alarms; Observer as scheduled job | Drift/cost/latency detection |
| **Compliance & Audits** | Immutable INSERT-ONLY audit log | Tamper-proof record |
| **Deployment Safety** | Config-activation deploy + instant rollback (Blue/Green → Phase 2) | Low-risk, reversible promotion |

---

# 04   Target Users & Personas

| Role | Key Pain Point | How AutoRAG Solves It |
| --- | --- | --- |
| **ML Engineer** | Days of manual parameter sweeps | Auto tuning + failure analysis (Diagnoser), all on a constant Q&A set |
| **Enterprise Lead** | Compliance, isolation, audit logs | Immutable log, org scoping, approval gates |
| **Data Scientist** | No datasets / objective metrics | Generate-once synthetic Q&A + RAGAS + experiment tracking |
| **Application Developer** | Needs simple query endpoints | Direct config API, single query REST endpoint |

---

# 05   Product Goals & Success Metrics

| KPI Metric | Target Value | Verification Source | Level |
| --- | --- | --- | --- |
| Unified Score — MVP acceptance | ≥ 0.80 | Evaluator | AI Quality |
| Unified Score — deploy gate | ≥ 0.85 | Evaluator | AI Quality |
| Retrieval Recall@5 | ≥ 0.85 | Evaluator (vs known source chunks) | AI Quality |
| Faithfulness — **hard gate** | ≥ 0.50 (non-bypassable) | Gemini Pro Judge | AI Quality |
| Faithfulness — quality target | ≥ 0.80 | Gemini Pro Judge | AI Quality |
| Adversarial fabrications (fixed anchors) | 0 | Injected eval run | AI Quality |
| Judge ↔ human correlation | ≥ 0.85 (validate W1–2) | Calibration run | AI Quality |
| Failure Classification Accuracy | ≥ 90% | Diagnoser logs | AI Quality |
| Pipeline Build (1,000 docs) | < 5 minutes | Ingestion logs | Efficiency |
| Evaluation Sweep (stored 50 Q&A) | < 8 minutes | Evaluator logs | Efficiency |
| p95 Query Latency (FastPath) | < 3 seconds | API logs | Efficiency |
| SLA Uptime | 99.5% | CloudWatch | Reliability |

---

# 06   Scope Definition

| In Scope (Phase 1 / MVP) | Planned (Phase 2) | Out of Scope / Never |
| --- | --- | --- |
| 9-agent model as 3 flows | Late Chunking (token-level embeddings) | Real-time streaming ingestion |
| Query FastPath (synchronous) | Blue/Green ECS canary + ALB shifting | Native mobile apps |
| **Optional** Query Rewriter / HyDE (flags, off by default) | Context Compressor; real-time Observer drift detection | On-prem fine-tuning |
| 2 Chunking strategies (Semantic, Hierarchical) | Agentic query mode (GA) | Write-back to source systems |
| Hybrid retrieval (pgvector + tsvector DB-level RRF + Cohere) | Multi-model integration | Custom embedding training |
| 3-Layer Eval against **static stored set** | SSO / SAML; RBAC | General data-cleaning utilities |
| Direct config API (no-code) | Configurator wizard UI | |
| Supabase (DB, pgvector, Storage, Auth) | Email/Resend approvals; 20-screen dashboard | |
| Config-activation deploy + instant rollback | SOC 2 Type II | |
| Tiered PII masking; CloudWatch | Multi-tenant workspace isolation | |
| 5-screen dashboard | | |

---

# 07   Solution Architecture — 9-Agent Model, 3 Execution Flows

The 9 agents are a **conceptual model**. They are implemented as **three flows** with different runtime characteristics. This separation is the single most important architectural decision in v3.0.

## 7.1  The Three Flows

**Flow 1 — Ingest (single background Celery pipeline; Builder folded into Ingestion):**
```
Ingestion (parse → PII mask → chunk → embed → index) → done
```

**Flow 2 — Query FastPath (synchronous Python pipeline in FastAPI — NOT LangGraph):**
```
Query Rewriter* → Hybrid Retrieval (DB-level RRF) → Cohere Rerank → Generation
   * = optional flag, off by default, bypassed for simple/clear queries
   HyDE = optional; triggered only when first-pass retrieval is weak (< 3 hits above threshold) or query is vague
   Context Compressor = deferred to Phase 2 (MVP passes the top-5 reranked chunks directly to the LLM)
```
> Rationale: a stateful graph with checkpoint writes adds 50–200ms per node. Live queries must be a lightweight function chain to hit p95 < 3s.

**Flow 3 — Optimization Loop (stateful LangGraph graph; asynchronous):**
```
Evaluator → Observer → Diagnoser → Improver → Deployer
```

## 7.2  Agent Specifications

> The 9 agents are a **conceptual model** retained for clarity and roadmap. For MVP they are implemented as **~5 build components** (see §7.2.1) — some agents are merged, demoted to optional flags, or stubbed. This keeps the "9-agent" story while drastically reducing the number of moving parts to build.

| Agent | Flow | Purpose | Primary Engine | MVP Status |
| --- | --- | --- | --- | --- |
| **Ingestion** | Ingest | Load, extract, tiered PII mask, chunk, **embed + index** | Rule-based + `gemini-embedding-001` | **Build** (absorbs Builder) |
| **Builder** | Ingest | Batch-embed, index to pgvector | `gemini-embedding-001` + pgvector | **Merged into Ingestion** |
| **Query Rewriter** | Query | Expand/clarify ambiguous queries | Gemini 2.5 Flash | Optional flag (off by default) |
| **Context Compressor** | Query | Trim retrieved context | Gemini 2.5 Flash | **Deferred to Phase 2** |
| **Evaluator** | Optimize | Score vs **stored static set**; **rule-based failure classification** | Gemini Pro (judge) + Flash (gen) | **Build** (absorbs MVP Diagnoser) |
| **Observer** | Optimize | Monitor drift/latency/cost | Metric-driven | Scheduled cron stub |
| **Diagnoser** | Optimize | Classify failures, specify remediations | Gemini 2.5 Pro | Rule-based inside Evaluator for MVP; LLM agent in Phase 2 |
| **Improver** | Optimize | Generate variants, test on constant set, submit for approval | Gemini Flash + Pro | **Build** (core differentiator) |
| **Deployer** | Optimize | **Activate config version + invalidate cache** (Blue/Green → Phase 2) | DB + cache | **Build** (lightweight) |

### 7.2.1  MVP Implementation Mapping (9 concepts → 5 components)

| MVP Component | Covers Agents | Notes |
| --- | --- | --- |
| **1. Ingestion Pipeline** | Ingestion + Builder | One Celery job: parse → PII → chunk → embed → index |
| **2. Query FastPath** | Query Rewriter*, HyDE*, retrieval + rerank | Synchronous; rewrite/HyDE optional flags; Context Compressor deferred |
| **3. Evaluator** | Evaluator + Diagnoser (rule-based) | Core scoring brain; rule-based failure classification |
| **4. Improver** | Improver | Core self-tuning brain |
| **5. Deployer** | Deployer | Config activation + instant rollback |
| *(stub)* **Observer** | Observer | Scheduled cron re-evaluating against the golden set |

> `*` optional flags, off by default to protect p95 < 3s. Invest the most engineering effort in components **3 and 4** — they are the differentiator.

## 7.3  Core Data & Memory Strategy

- **Checkpoints**: Only the **optimization loop** uses LangGraph `PostgresSaver`. PII-bearing fields are stripped before checkpoint writes.
- **Vector Storage**: chunk embeddings in `chunk_embeddings` (768-dim).
- **Relational Metadata**: pipelines, runs, evaluations, experiments, deployments, query logs, audit logs, **golden_datasets**.
- **Object Storage**: raw files + parsed artifacts in Supabase Storage.

---

# 08   Feature Specifications

## 8.1  F1 — Chunking (2 Strategies for MVP)

- **Semantic Chunking**: split at embedding-similarity drops between sentence windows. Default for narrative text.
- **Hierarchical Chunking**: parent chunks (1024 tokens) with child chunks (128 tokens); index children, retrieve parents to avoid context overflow.
- **Late Chunking**: **deferred to Phase 2** — requires a token-level embedding model (e.g., `jina-embeddings-v3` with `late_chunking=True`); not implementable with single-vector embedding APIs.
- **Auto-router**: `> 50 pages → hierarchical`, else `semantic`.

## 8.2  F2 — Retrieval Pipeline

1. **Hybrid Retrieval (single DB call)**: pgvector dense + tsvector keyword fused via a **PL/pgSQL `hybrid_search_rrf` function** (RRF, k=60), over-fetching top-20.
2. **Cross-Encoder Reranking**: Cohere Rerank v3.5 → top-5. **Graceful degradation**: on Cohere failure, return un-reranked results and log a warning.
3. **HyDE (conditional)**: only when first-pass retrieval returns < 3 results above similarity 0.7, or the Query Rewriter flags the query as abstract/vague.

## 8.3  F3 — 3-Layer Evaluation Stack (Static Set)

- **Static Q&A baseline**: generate 50 synthetic Q&A **once** per pipeline (at first evaluation), store in `golden_datasets`. All subsequent runs — including Improver variant tests — use the **same** stored set for reproducible comparison and near-zero generation cost.
- **Layer 1 — Unified Score Gate**:
  $$\text{Score} = 0.25\,\text{Retrieval} + 0.35\,\text{Quality} + 0.25\,\text{Faithfulness} - 0.10\,\text{Latency} - 0.05\,\text{Cost}$$
- **Layer 2 — RAGAS Metrics**: Context Precision, Context Recall, Faithfulness, Answer Relevancy. *(RAGAS+Gemini compatibility validated Week 1; GPT-4o scoring fallback if correlation < 0.70.)*
- **Layer 3 — Adversarial Validation**: **5 fixed anchor questions** (regression) + **5 dynamically generated** per run. Any fabricated fact on the fixed anchors blocks deployment.
- **Judge Reasoning**: Gemini 2.5 Pro returns `{score, reasoning}` (chain-of-thought).

## 8.4  F4 — Agentic Query Mode (Optional)

An optional iterative retrieval mode (Phase 2 GA): generate queries → search → LLM judges "can I answer with these chunks?" → if not, re-query up to `maxEvals` within a token budget. Pattern validated by production open-source RAG systems; kept optional so the default FastPath stays fast.

---

# 09   API & Integration Requirements

## 9.1  REST Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/ingest` | Process, mask, chunk, store document files |
| `POST` | `/api/v1/pipelines` | Create/compile a pipeline config (direct JSON/YAML) |
| `POST` | `/api/v1/pipelines/{id}/evaluate` | Run 3-layer evaluation against the stored set |
| `GET`  | `/api/v1/score/{run_id}` | Retrieve a run's scores |
| `GET`  | `/api/v1/observe` | Cost, latency, drift metrics for a pipeline |
| `POST` | `/api/v1/diagnose` | Classify failures and retrieve suggestions |
| `POST` | `/api/v1/improve` | Generate + evaluate variants on the constant set |
| `POST` | `/api/v1/approve` | Submit manual approval (dashboard) |
| `GET`  | `/api/v1/experiments` | List experiment runs and score deltas |
| `POST` | `/api/v1/experiments/compare` | Compare two runs side-by-side |
| `POST` | `/api/v1/query` | Execute FastPath search + generation (SSE streaming) |
| `POST` | `/api/v1/deploy/{run_id}` | Activate a healthy pipeline config version |
| `POST` | `/api/v1/deploy/rollback` | Revert active pipeline version |
| `GET`  | `/api/v1/jobs/{job_id}` | Async Celery task status |
| `GET`  | `/api/v1/audit-log` | Query immutable audit events |

## 9.2  Integration Map

- **Gemini API**: embeddings (`gemini-embedding-001`) + LLM (Pro judge, Flash fast ops).
- **OpenAI API**: GPT-4o failover; **RAGAS scoring fallback**.
- **Cohere API**: Rerank v3.5 (graceful degradation).
- **Supabase**: relational, pgvector, Storage, Auth.
- **AWS**: ECR images, ECS Fargate (single rolling service for MVP), CloudWatch.

---

# 10   Data & Storage Design

## 10.1  Storage Configurations

| Component | Technology | Target environment |
| --- | --- | --- |
| Relational DB | Supabase PostgreSQL | Config, audit, runs, golden set |
| Vector DB | Supabase pgvector | Cosine HNSW index |
| File Storage | Supabase Storage | Document buckets |
| Cache & Broker | Redis | Prefixed: `celery:`, `cache:`, `session:` |

## 10.2  Core Schema (12 Tables)

`pipelines`, `pipeline_runs`, `evaluations`, `experiments`, `deployments`, `audit_log`, `query_logs`, `documents` (with **status** column), `chunk_embeddings`, `agent_retries`, `doc_relationships`, **`golden_datasets`** (new — see LLD §3). `pipeline_runs` gains a **`prompt_versions JSONB`** column for traceability.

---

# 11   Non-Functional Requirements

## 11.1  Operational SLOs

| Metric | Target Value | Detail |
| --- | --- | --- |
| `/query` p50 | < 1.0s | Cached < 150ms |
| `/query` p95 | < 3.0s | Uncached + rerank (FastPath, conditional stages off) |
| `/query` p99 | < 5.0s | Gateway timeout |
| Ingestion (1,000 docs) | < 5 min | Batch embedding (100/req, 5 concurrent) |
| Evaluation (stored set) | < 8 min | RAGAS + judge |
| Dashboard FCP | < 2.0s | |

## 11.2  Data Privacy & Security

- **Tiered PII**: Tier 1 regex (email, phone, SSN/Aadhaar, credit card, IP); Tier 2 optional Gemini Flash structured check on sampled chunks for sensitive docs.
- **Org scoping**: `organization_id` on every query (RLS deferred to Phase 2).
- **Immutable audit**: RULEs block UPDATE/DELETE on `audit_log`.

---

# 12   AI Safety & Governance

- **Hard Deployment Gate**: Faithfulness < 0.50 OR any fabrication on fixed adversarial anchors → BLOCKED (non-bypassable).
- **Quality target vs hard gate** are distinct: ≥ 0.80 is the aspiration that triggers improvement; ≥ 0.50 is the absolute floor.
- **Model/prompt changes** are high-risk → mandatory reviewer sign-off.
- **Prompt Isolation**: XML-delimited inputs; structured JSON-schema outputs validated to prevent injection.

---

# 13   Monitoring, Observability & LLMOps

- **Structured JSON logs** from FastAPI + Celery (never log raw query/doc text, keys, or PII).
- **Custom metrics**: latency, error rates, cost, Unified Score.
- **Alarms**: errors > 1%, Unified Score drop > 0.05.
- **Observer (MVP)**: a **scheduled job (every 6h)** that evaluates a sample of recent queries; real-time drift detection is Phase 2.

---

# 14   Testing Strategy

| Component | Target Coverage | Method |
| --- | --- | --- |
| Core Scoring Functions | 95% | Pytest |
| Optimization-loop nodes | 90% | Mocked graph runs |
| Integration Gateway | 80% | Pytest client |
| **RAGAS+Gemini correlation** | n/a | **Week-1 calibration test (≥0.85 target)** |

---

# 15   UX & UI Requirements

The MVP dashboard is **5 screens** (Next.js): **Pipeline List**, **Score Card**, **Query Playground**, **Experiment List**, **Audit Log**. Brand: Purple (`#5B21B6`) primary, Navy (`#1E1B4B`) headings, Orange (`#F97316`) accents. Score color-coding: Green (≥0.85), Amber (0.70–0.84), Red (<0.70). Ingestion progress streams via the document **status state machine** (`queued → pre_processing → processing → completed/failed`).

---

# 16   Deployment & DevOps

**MVP**: a single rolling ECS Fargate service per component (api, worker, dashboard). "Deploying a pipeline" = **activating a config version row + invalidating cache**; rollback = pointing back to the previous active version (instant, reversible). **Blue/Green ECS with ALB traffic shifting and canary is Phase 2.**

---

# 17   Timeline & Milestones — 7-Week Plan

| Week | Focus | Deliverables |
| --- | --- | --- |
| **W1** | Foundation + eval de-risk | Schema, FastPath skeleton, RAGAS+Gemini test, golden set table |
| **W2** | Ingestion & retrieval | Parsing, tiered PII, batch embedding, pgvector + DB-level RRF |
| **W3** | Static evaluation | Evaluator (generate+store set), RAGAS, judge, Unified Score |
| **W4** | Optimization loop | LangGraph Observer(cron)→Diagnoser→Improver→Deployer |
| **W5** | Dashboard (5 screens) | List, score card, query playground, experiments, audit |
| **W6** | Calibration & testing | Golden-set calibration, regression, observability |
| **W7** | Hardening & launch | Security, FastPath load test, release |

---

# 18   Business Model, Pricing & ROI

| License Tier | Audience | Price | Features |
| --- | --- | --- | --- |
| Open Source | Developers | Free (MIT) | 3-flow core, APIs, self-hosted |
| Pro | Scaling Teams | ₹3 Lakh / yr | Email support, managed updates, audit logs |
| Enterprise | Corporate | ₹12–25 Lakh / yr | Dedicated support, SLA, SSO/RBAC |
| Managed Cloud | SaaS | ₹25–60 Lakh / yr | Managed hosting, autoscaling |

---

# 19   Go-To-Market Strategy

- **Direct Pilots** with enterprise partners for case studies.
- **Developer Adoption** via open-source + docs.
- **Cloud Marketplaces** (AWS Marketplace ECS template).

---

# 20   Risks & Architectural Guidelines

- **RAGAS+Gemini**: validate compatibility Week 1; GPT-4o scoring fallback if needed.
- **FastPath latency**: keep query path synchronous; conditional stages off by default.
- **Checkpoint hygiene**: strip PII before optimization-loop checkpoint writes.
- **Supabase scaling**: partition tables for high-volume; `ef_search=128`.
- **Reranker failure**: bypass rerank, serve hybrid results, log warning.
- **Provider abstraction**: embedding/rerank/LLM behind abstract base classes for easy provider swaps.

---

# 21   Engineering Operations

- **Onboarding**: `docker compose up`, `/health`, Pytest.
- **Quality Gates**: Ruff + mypy clean; ≥ 80% coverage before merge.
- **Cadence**: weekly automated eval against the golden set; log Unified Scores + latency.
- **Patterns to adopt**: graceful degradation, batch+retry embedding, Pydantic-validated task payloads, rate limiting on external APIs, `assert_never` for provider routing.

---

# 22   Sign-Off

| Role | Title / Name | Signature | Date |
| --- | --- | --- | --- |
| Product Owner | — | — | — |
| Lead Engineer | — | — | — |
| Security Officer | — | — | — |
| Executive Sponsor | — | — | — |

---
*AutoRAG Platform — Approved Technical Specification (v3.0, MVP-Hardened). Proprietary and Confidential.*
