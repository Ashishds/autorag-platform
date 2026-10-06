# AutoRAG Architect — Business Requirements Document

**Version**: 2.0 (MVP-Hardened Revision) | **Classification**: Proprietary & Confidential
**Project**: AutoRAG Architect
**Date**: May 2026 | **Status**: Approved
**Supersedes**: BRD v1.0 — revised to reduce MVP delivery risk based on architecture review

---

## 0. Revision Notes (v1.0 → v2.0)

This revision keeps the business vision intact but hardens the plan for a **realistic, shippable MVP with high accuracy**. Key changes:

| Change | Reason |
|--------|--------|
| Query-time pipeline runs as a **synchronous FastPath** (not a stateful agent graph) | Meet p95 < 3s; avoid orchestration overhead on live requests |
| **2 chunking strategies** for MVP (Semantic + Hierarchical); Late Chunking deferred | Late Chunking is not implementable with single-vector embedding APIs |
| **Static, stored evaluation set** (generate once, reuse) | Reproducible variant comparison; eliminates runaway LLM cost |
| **Tiered PII** (regex + optional LLM verification) | Regex alone misses contextual PII; claims now match implementation |
| **Simplified MVP deployment** (config activation + instant rollback); Blue/Green ECS canary → Phase 2 | A pipeline change is config + data, not application code |
| **Reconciled quality thresholds** across all docs | v1.0 had conflicting Faithfulness/Unified Score targets |
| **Observer runs as a scheduled job** for MVP | No meaningful production traffic exists at MVP to drive real-time drift |

---

## 1. Executive Summary

**AutoRAG Architect** is an enterprise-grade, closed-loop autonomous AI platform that builds, evaluates, diagnoses, improves, and ships Retrieval-Augmented Generation (RAG) pipelines with minimal manual intervention.

**The business problem**: Tuning RAG systems manually is labor-intensive — often days per iteration — without objective quality metrics, safe rollback, or production monitoring. AutoRAG Architect introduces a **conceptual 9-agent model organized into three concrete flows** (ingest, query, optimize) that reduces time-to-first-deployment from weeks to hours while enforcing objective quality.

**Core value proposition**: A weighted, non-bypassable **Unified Score gate** governs every promotion to production. No pipeline configuration is promoted without passing strict quality thresholds, ensuring a secure, reliable, self-improving retrieval loop.

**What makes us different**: Unlike RAG runtimes/hosting platforms (e.g., open-source RAG servers), AutoRAG's differentiator is the **evaluation + self-improvement layer** — Unified Score, RAGAS metrics, adversarial testing, and an automated diagnose→improve loop. The ingestion/retrieval layer is intentionally pragmatic; the *quality brain* is the product.

---

## 2. Business Problem

| Pain Point | Business & Operational Impact |
|-----------|------------------------------|
| Manual tuning across RAG layers (chunking, embedding, retrieval, prompts, evaluation) | High engineering overhead; delayed launch cycles |
| No objective scoring — quality judged ad-hoc | No guarantee of pipeline performance or reliability |
| No comprehensive production observability | Quality drift discovered by end-users, not systems |
| No reliable quality gate at build time | Risk of shipping hallucinated or incomplete answers |
| No automated rollback | Manual redeployments cause downtime |

**Market Opportunity**: Falling LLM API costs, mature agentic frameworks (LangGraph), and unified database architectures (Supabase PostgreSQL + pgvector) make closed-loop, self-optimizing RAG commercially viable.

---

## 3. Business Objectives

### Phase 1 — Core Platform Release (MVP)

| Objective | Success Criterion |
|-----------|--------------------|
| Deliver an autonomous build→evaluate→improve loop | Unified Score **≥ 0.80** on the golden validation set |
| Eliminate manual hyperparameter tuning | Reduce ingestion-to-deployment-preparation time to **≤ 4 hours** |
| Establish a non-bypassable deployment quality gate | Enforce **Unified Score ≥ 0.85** AND **Faithfulness ≥ 0.50 (hard gate)** for all promotions |
| Enable safe rollbacks | Instant config rollback (revert active pipeline version); error/latency alarms |
| Provide audit-grade compliance | Tiered PII masking at ingestion boundary; immutable INSERT-ONLY audit log |

> **Threshold reconciliation (authoritative for all docs):**
> - **Unified Score:** ≥ 0.85 → deploy-eligible · 0.70–0.84 → improvement loop · < 0.70 → hard block
> - **Faithfulness:** ≥ 0.50 → **hard gate** (below = BLOCKED, non-bypassable) · ≥ 0.80 → quality target (below but ≥0.50 contributes to improvement trigger)
> - **Adversarial:** zero fabrications on the fixed anchor set → hard gate
> - **MVP golden-set acceptance:** Unified Score ≥ 0.80

### Phase 2 — Enterprise Scaling
- Multi-model configurations (Gemini, OpenAI, Mistral); Late Chunking with a token-level embedding model.
- Blue/Green ECS canary deployment with auto-rollback.
- RBAC, SSO, federated data sources; real-time Observer drift detection.

### Phase 3 — Enterprise Cloud SaaS
- Managed cloud, multi-tenant workspace isolation, HA clusters, usage-based billing.

---

## 4. Target Users & Personas

| Role | Operational Pain Point | Platform Solution |
|---------|-----------|------------------|
| **ML Engineer** | High iteration overhead; no standard metrics | Automated variant testing against a constant Q&A set + Unified Score gate; Diagnoser isolates failures |
| **Enterprise Lead / Compliance Officer** | Compliance risk; needs audit trails | Approval gates, immutable audit logging, instant rollback |
| **Data Scientist** | High cost of manual labeling/tracking | Generate-once synthetic Q&A + reproducible experiment tracking |
| **Application Developer** | Complexity of orchestrating RAG services | Direct config API, automated deployment, unified query endpoint |

---

## 5. Scope

### In Scope — Phase 1 (MVP)

- **Conceptual 9-Agent model implemented as 3 flows**:
  - **Ingest flow** (background job): Ingestion → Builder.
  - **Query flow (FastPath)** (synchronous): Query Rewriter* → Hybrid Retrieval → Rerank → (Context Compressor*) → Generation. *(\*conditional/optional)*
  - **Optimization loop** (LangGraph): Evaluator → Observer → Diagnoser → Improver → Deployer.
- **2 Chunking Strategies**: Semantic, Hierarchical (parent/child).
- **Hybrid Retrieval**: pgvector dense + tsvector keyword fused via **database-level Reciprocal Rank Fusion**, then Cohere Rerank; **conditional HyDE**.
- **3-Layer Evaluation Stack**: Unified Score, RAGAS metrics, adversarial Q&A — run against a **stored static golden set**.
- **Tiered PII Masking**: regex (Tier 1) + optional Gemini Flash verification (Tier 2) at ingestion boundary.
- **MVP Deployment**: pipeline activation (config row + cache invalidation) with instant rollback.
- **Immutable Auditing**: append-only PostgreSQL audit table; internal lifecycle events.
- **Observability**: CloudWatch logs/metrics/alarms; Observer as a scheduled job.
- **Unified Data Platform**: Supabase PostgreSQL, pgvector HNSW, Supabase Storage, Supabase Auth.
- **Dashboard**: **5 essential Next.js screens** (pipeline list, score card, query playground, experiment list, audit log).

### Out of Scope — Phase 1

- Late Chunking (needs token-level embeddings).
- Blue/Green ECS canary with ALB traffic shifting (config-activation rollback is used instead).
- Real-time Observer drift detection; 20-screen dashboard; email/Resend approvals (dashboard-only for MVP).
- Configurator wizard UI (direct config API for MVP); multi-tenant billing; Kubernetes; native mobile.

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Operational DB** | Supabase PostgreSQL | Pipeline configs, runs, evaluations, audit trail, golden set, checkpoints |
| **Vector DB** | Supabase pgvector (HNSW) | 768-dim Gemini embeddings, cosine similarity |
| **Hybrid Search** | pgvector + tsvector + **DB-level RRF function** | Single-call dense + keyword fusion |
| **Object Storage** | Supabase Storage | Raw documents + parsed artifacts |
| **Auth** | Supabase Auth | JWT, sessions, organization scoping |
| **DB Access** | `supabase-py` (CRUD) + `asyncpg` (vector/bulk) + Alembic (migrations) | No heavy ORM; raw SQL where it matters |
| **Embedding Model** | `gemini-embedding-001` (768-dim via MRL truncation) | Primary embeddings |
| **LLM Primary** | Gemini 2.5 Pro (judge) + Flash (fast ops) | Reasoning + high-volume tasks |
| **LLM Fallback** | OpenAI GPT-4o | Failover; also RAGAS scoring fallback |
| **Orchestration** | **LangGraph (optimization loop only)** + Celery (async jobs) | Stateful loop + background tasks |
| **Broker/Cache** | Redis (prefixed: `celery:`, `cache:`, `session:`) | Queue, rerank cache, sessions |
| **Reranker** | Cohere Rerank v3.5 (graceful degradation) | Cross-encoder precision |
| **PII Detection** | Tiered (regex + optional Gemini Flash) | Boundary masking |
| **Doc Parsing** | Unstructured.io | Multi-format extraction |
| **Evaluation** | RAGAS + Gemini Judge (GPT-4o scoring fallback) | Standard metrics + Unified Score |
| **Backend** | FastAPI (Python 3.12) | REST + SSE streaming |
| **Frontend** | Next.js 14/15 (TypeScript) | 5-screen admin dashboard |
| **Package Manager** | uv | Fast, locked dependency management |
| **Deployment** | ECS Fargate + ECR (single rolling service for MVP) | Serverless containers |
| **CI/CD** | GitHub Actions | Build, test, deploy |
| **Monitoring** | AWS CloudWatch | Logs, metrics, alarms |

---

## 7. Business Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| **BR-01** | Users configure and compile a complete pipeline via a direct config API (no code). | Must Have |
| **BR-02** | Every promotion passes a non-bypassable gate: Unified Score ≥ 0.85 AND Faithfulness ≥ 0.50. | Must Have |
| **BR-03** | Changes scoring 0.70–0.84 require manual stakeholder approval via the dashboard. | Must Have |
| **BR-04** | All source files are PII-scanned and masked at the boundary before any external LLM/vector write. | Must Have |
| **BR-05** | All events/actions are logged in an immutable, append-only audit trail (no UPDATE/DELETE). | Must Have |
| **BR-06** | When quality degrades, the platform runs evaluation against the stored set, classifies failures, and suggests variant fixes. | Must Have |
| **BR-07** | Variant comparisons must use the **same stored Q&A set** for reproducibility. | Must Have |
| **BR-08** | Promotions are reversible via instant config rollback. | Must Have |
| **BR-09** | End-to-end from upload to active, monitored pipeline completes in ≤ 4 hours. | Must Have |

---

## 8. Success Metrics

| Category | Metric | Phase 1 Target |
|---------|--------|----------------|
| **AI Quality** | Unified Score (golden set) | ≥ 0.80 (MVP acceptance) / ≥ 0.85 (deploy gate) |
| **AI Quality** | Faithfulness — hard gate | ≥ 0.50 (non-bypassable) |
| **AI Quality** | Faithfulness — quality target | ≥ 0.80 |
| **AI Quality** | Adversarial fabrications (fixed anchors) | 0 |
| **AI Quality** | Judge ↔ human correlation | ≥ 0.85 (validate Week 1–2) |
| **Operational** | p95 Query Latency (FastPath) | < 3 seconds |
| **Operational** | Ingestion & Build (1,000 docs) | < 5 minutes |
| **Business** | Setup-to-Active Time | ≤ 4 hours |

---

## 9. Security & Compliance

| Area | Control | Implementation |
|------|---------|---------------|
| **User Access** | Supabase Auth | Login flows, JWT verification, session timeouts |
| **Authorization** | Organization scoping | `organization_id` filter on every query (RLS in Phase 2) |
| **PII Shielding** | Tiered PII pipeline | Regex Tier 1 + optional Gemini Flash Tier 2 at ingestion boundary |
| **Audit Immutability** | Append-only tables | PostgreSQL RULEs blocking UPDATE/DELETE |
| **Secrets** | AWS Secrets Manager | Keys injected at container level; never in VCS |
| **Transit** | HTTPS / TLS 1.3 | Encrypted everywhere |

**MVP PII set (explicit):** email, phone (with country codes), SSN/Aadhaar, credit card (Luhn + regex), IP address. **Deferred to Phase 2 (NER-based):** names, addresses, dates of birth.

---

## 10. Estimated Infrastructure Cost (Monthly Target)

| Service Component | Estimated Monthly Cost | Details |
|---------|----------------------|-------|
| Supabase (Pro) | $25 | DB, pgvector, Storage, Auth |
| Gemini API | $50–100 | Pro judge + Flash fast ops |
| OpenAI API (fallback + RAGAS scoring) | $10–30 | Failover + eval scoring |
| Cohere Rerank | $10–20 | Cross-encoder |
| AWS ECS Fargate | $80–150 | API, workers, dashboard |
| Redis (ElastiCache) | $30 | cache.t3.medium |
| AWS CloudWatch | $10–20 | Logs + metrics |
| **Target Total** | **~$215–375 / month** | Phase 1 MVP |

> **Cost control:** The static stored Q&A set means variant evaluations reuse the same questions — synthetic generation cost drops to ~zero after the first run. Embedding is batched (100/req) and rate-limited.

---

## 11. Key Constraints & Risks

### Constraints
- **Timeline**: 7-week target (see §12) with a ruthlessly scoped MVP; Phase 2 absorbs deferred items.
- **Architecture**: AWS ECS Fargate (single rolling service for MVP).
- **Compliance**: No plain-text raw PII written to vector spaces or logs.

### Operational Risks & Mitigation

| Risk Event | Impact | Mitigation |
|------|-----------|---------------------|
| **RAGAS+Gemini scores don't correlate with humans** | High | **Validate in Week 1–2** on 5–10 pairs; fall back to GPT-4o for scoring only if correlation < 0.70 |
| AI judgment diverges from human eval | High | Calibrate against golden set; target ≥ 0.85 correlation |
| Vector search degrades at scale | Medium | HNSW (m=16, ef_construct=200), DB-level RRF, rerank cache |
| PII masking misses non-standard PII | Medium | Tier 2 LLM check on sampled chunks for sensitive docs; log anomalies |
| Primary LLM outage / rate limits | High | Circuit-breaker failover to GPT-4o; embedding rate limiting |
| Reranker (Cohere) downtime | Low | Graceful degradation — return un-reranked results, log warning |

---

## 12. Delivery Timeline (Revised, Risk-Aligned)

| Week | Phase Focus | Key Milestones |
|------|------------|----------------|
| **W1** | Foundation + Eval De-risk | Supabase schema, FastPath skeleton, **RAGAS+Gemini compatibility test**, golden set table |
| **W2** | Ingestion & Retrieval | Unstructured.io parsing, tiered PII, batch embedding, pgvector + DB-level RRF hybrid search |
| **W3** | Static Evaluation | Evaluator: generate+store static Q&A, RAGAS, Gemini judge, Unified Score |
| **W4** | Optimization Loop | LangGraph graph for Observer(cron)→Diagnoser→Improver→Deployer (config activation) |
| **W5** | Dashboard (5 screens) | Pipeline list, score card, query playground, experiments, audit log |
| **W6** | Calibration & QA | Golden-set calibration (≥0.85 correlation), regression runs, CloudWatch alarms |
| **W7** | Hardening & Launch | Security review, load test of FastPath, production release |

> If any week slips, the **first cuts** are: HyDE (already conditional), Context Compressor (pass top-5 directly), and dashboard screens beyond the core 3 (list, score card, query playground).

---

## 13. Project Sign-Off

| Stakeholder Role | Name / Title | Signature | Date |
| --- | --- | --- | --- |
| **Product Owner** | — | — | — |
| **Lead Engineer** | — | — | — |
| **Security Officer** | — | — | — |
| **Executive Sponsor** | — | — | — |

---
*AutoRAG Architect — Approved Technical Specification (v2.0, MVP-Hardened). Proprietary and Confidential.*
