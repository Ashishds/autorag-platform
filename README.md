<div align="center">

# ⚡ AutoRAG
### Enterprise Autonomous RAG Optimization & Self-Healing Platform

**Self-evaluating, self-optimizing Retrieval-Augmented Generation engine powered by hybrid retrieval, multi-provider LLM orchestration, and non-bypassable quality guardrails.**

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.0-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%7C%2017-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW%20Vector%20Search-3FCF8E?logo=supabase&logoColor=white)](https://github.com/pgvector/pgvector)
[![LangGraph](https://img.shields.io/badge/LangGraph-Self--Healing%20Loop-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![Celery](https://img.shields.io/badge/Celery-Distributed%20Workers-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

<br/>

[Key Features](#-key-features) •
[Architecture](#-enterprise-architecture) •
[Quickstart (No Docker)](#-quick-start--local-without-docker) •
[Docker Deployment](#-containerized-deployment-docker) •
[API Reference](#-api-reference) •
[Design Specs](#-authoritative-specifications--documentation)

---

</div>

## 📌 Executive Overview

Traditional enterprise RAG implementations suffer from **fragile manual tuning**: engineering teams continuously tweak chunk sizes, re-embed collections, swap rerankers, and inspect arbitrary query samples with high operational cost and no statistical certainty.

**AutoRAG transforms RAG engineering into an autonomous, closed-loop optimization system.** It ingests heterogeneous enterprise documents, builds an optimized hybrid-retrieval pipeline, scores retrieval and answer quality against a frozen golden evaluation set, diagnoses failures, automatically searches for superior parameter configurations, and safely promotes candidates into production behind hard verification gates.

---

## 🌟 Key Features

### 1. Ingestion & Multi-Format Parsing
* **Universal Document Ingestion**: Native extraction for PDF, DOCX, PPTX, CSV, Excel, TXT, Markdown, HTML, and YouTube transcripts.
* **Enterprise Cloud Connectors**: Sync pipelines with Google Drive, Notion, Dropbox, and Microsoft OneDrive/SharePoint via OAuth2.
* **Integrated PII Anonymization**: Automatic masking of sensitive identifiers (SSN, credit cards, emails, phone numbers) before chunking and embedding.
* **Adaptive Chunking**: Hierarchical and semantic boundary chunking preserving contextual parent-child relationships.

### 2. High-Precision Hybrid Retrieval
* **DB-Level Reciprocal Rank Fusion (RRF)**: Combines dense vector similarity (`pgvector` HNSW index, 768-dim embeddings) and sparse lexical search (`tsvector` BM25 full-text) directly inside PostgreSQL.
* **Cross-Encoder Re-Ranking**: Integrated Cohere Rerank v3.5 with automated **graceful degradation** to native RRF rank if external providers experience latency spikes.
* **Query Transformation**: Optional HyDE (Hypothetical Document Embeddings) and sub-query decomposition.

### 3. Closed-Loop Autonomous Optimization
* **Frozen Golden Datasets**: Pipeline variations are benchmarked strictly against identical reference anchors to eliminate evaluation variance.
* **Unified Quality Score**:
  $$\text{Unified Score} = 0.25 \cdot \text{Retrieval} + 0.35 \cdot \text{Quality} + 0.25 \cdot \text{Faithfulness} - 0.10 \cdot \text{Latency} - 0.05 \cdot \text{Cost}$$
* **Self-Healing Loop (LangGraph)**: Evaluates $\rightarrow$ Diagnoses root causes (e.g. low context recall vs. generator hallucination) $\rightarrow$ Proposes hyperparameter changes $\rightarrow$ Validates new variants.

### 4. Non-Bypassable Enterprise Guardrails
* **Zero-Hallucination Gate**: Faithfulness threshold hard gate ($\ge 0.50$ baseline, configurable $\ge 0.72$ for production promotion).
* **Adversarial Anchor Tests**: 100% pass requirement on adversarial test scenarios before any config can be promoted.
* **Instant Rollbacks**: Versioned config deployments allow single-click reversion to the previous stable state.

---

## 🏗️ Enterprise Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["Frontend & Client Layer"]
        UI["Next.js 15 Web Console<br/>(Dashboard · Playground · Pipeline Studio)"]
        Widget["Embeddable Production Widget"]
    end

    subgraph FastPath["Query FastPath (Synchronous FastAPI · Sub-Second)"]
        direction TB
        QR["Query Normalizer & Rewrite (Optional)"]
        HR["Hybrid Retrieval<br/>(PostgreSQL RRF: pgvector HNSW + tsvector)"]
        RR["Cross-Encoder Reranker<br/>(Cohere v3.5 · Graceful Fallback)"]
        LLM["Generative LLM<br/>(Gemini 2.5 / GPT-4o with Citations)"]
        QR --> HR --> RR --> LLM
    end

    subgraph AsyncWorker["Async Processing (Celery Workers + Redis)"]
        ING["Document Ingestion<br/>Parse → PII Mask → Chunk → Embed"]
        CONN["Cloud Sync Connectors<br/>(Drive, Notion, Dropbox, OneDrive)"]
    end

    subgraph OptimizationEngine["Flow 3 · Autonomous Loop (LangGraph Checkpointed)"]
        direction LR
        EVAL["Evaluator Node<br/>(RAGAS + Faithfulness)"] --> DIAG["Rule-Based Diagnoser"]
        DIAG --> IMP["Improver Node<br/>(LLM-Driven Config Tuning)"]
        IMP --> TEST["Candidate Benchmark"]
        TEST --> GATE{"Faithfulness &<br/>Anchor Gate"}
        GATE -- Pass --> DEP["Production Deployer"]
        GATE -- Reject --> IMP
    end

    subgraph Persistence["Storage & Database Layer"]
        PG[("Supabase / PostgreSQL 16+<br/>• pgvector (HNSW 768d)<br/>• tsvector Full-Text<br/>• Pipeline Configs & Runs")]
        REDIS[("Redis 7 / Memurai<br/>• Task Queues<br/>• Result Backend<br/>• Caching")]
    end

    UI --> FastPath
    Widget --> FastPath
    ClientLayer --> AsyncWorker
    FastPath --> PG
    AsyncWorker --> PG
    AsyncWorker --> REDIS
    OptimizationEngine --> PG
    OptimizationEngine --> REDIS
```

---

## 💻 Tech Stack

| Domain | Enterprise Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** (Python 3.12+) | High-throughput asynchronous REST API |
| **Worker Engine** | **Celery** + **Redis** | Distributed document parsing, background sync, and evaluation |
| **Loop Orchestration** | **LangGraph** | Checkpointed stateful optimization loop |
| **Database & Vector** | **Supabase / PostgreSQL 16+** | `pgvector` HNSW indexes + `tsvector` full-text search (No ORM, high-speed `asyncpg`) |
| **Frontend UI** | **Next.js 15** (React 18, Tailwind CSS, Lucide) | Enterprise admin control panel, playground, and audit logs |
| **Embeddings & LLMs** | **Gemini 2.5 Flash / Pro**, **GPT-4o**, **Cohere** | Scalable embeddings (768-dim) and cross-encoder re-ranking |
| **Package Management** | **uv** & **npm** | Ultra-fast reproducible builds |

---

## 🚀 Quick Start — Local Without Docker

The project is fully pre-configured to run on Windows, macOS, or Linux natively without container overhead.

### Prerequisites
* **Python 3.12+** with [`uv`](https://docs.astral.sh/uv/) installed
* **Node.js 18+** with `npm`
* **Redis** (Local Redis server or [Memurai](https://www.memurai.com/) on Windows)
* **PostgreSQL with pgvector** (or free [Supabase](https://supabase.com/) project)

---

### Step 1: Environment Setup

Clone the repository and copy the environment template:

```bash
cd AutoRAG
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Configure your API keys and database credentials in `backend/.env`:
```ini
POSTGRES_URL=postgresql://user:password@localhost:5432/autorag
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
COHERE_API_KEY=your-cohere-api-key
```

---

### Step 2: One-Click Launch (Windows PowerShell)

Run the included automated launcher:
```powershell
.\start_local.ps1
```
*This verifies Redis on port `6379`, and launches the FastAPI backend, Celery worker (`--pool=solo`), and Next.js frontend in coordinated processes.*

To cleanly terminate all running local processes:
```powershell
.\stop_local.ps1
```

---

### Step 3: Manual Step-by-Step Launch (Any OS)

**1. Database Migrations:**
```bash
cd backend
uv run alembic upgrade head
```

**2. Start Backend API:**
```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**3. Start Celery Background Worker:**
```bash
cd backend
# Windows:
uv run celery -A app.workers.celery_app.celery worker --loglevel=info --pool=solo
# Linux/macOS:
uv run celery -A app.workers.celery_app.celery worker --loglevel=info
```

**4. Start Frontend Console:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🐳 Containerized Deployment (Docker)

To deploy the entire production stack using Docker Compose:

```bash
docker compose up -d
```

This provisions:
- `db`: PostgreSQL 16 with `pgvector` extension
- `redis`: Redis 7 Alpine
- `api`: FastAPI application on port `8000`
- `worker`: Celery distributed worker
- `beat`: Celery scheduled tasks
- `frontend`: Next.js 15 SSR application on port `3000`

---

## 🌐 Endpoints & Web Interface

| Component | Target URL | Description |
| :--- | :--- | :--- |
| **Frontend Application** | [http://localhost:3000](http://localhost:3000) | Full management console |
| **Interactive Dashboard** | [http://localhost:3000/dashboard](http://localhost:3000/dashboard) | Real-time pipeline metrics |
| **Document Management** | [http://localhost:3000/documents](http://localhost:3000/documents) | Document upload & chunk inspection |
| **Query Playground** | [http://localhost:3000/playground](http://localhost:3000/playground) | Interactive RAG testing with citations |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI specifications |
| **API Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Uptime & service version check |

---

## 🔌 API Reference

### 1. Ingest Documents
```http
POST /api/v1/ingest/upload
Content-Type: multipart/form-data

file: <document.pdf>
pipeline_id: <uuid>
chunking_strategy: "semantic"
```

### 2. Synchronous Query FastPath
```http
POST /api/v1/query
Content-Type: application/json

{
  "pipeline_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "query": "What are our regulatory compliance standards for PII?",
  "top_k": 5,
  "enable_rerank": true,
  "enable_rewrite": false
}
```

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "answer": "All PII data must be anonymized before ingestion under standard ISO/IEC 27001...",
    "citations": [
      {
        "document_id": "8b23c4a2-...",
        "chunk_id": "f47ac10b-...",
        "score": 0.942,
        "content": "...strict anonymization of customer identifiers..."
      }
    ],
    "latency_ms": 312,
    "model_used": "gemini-2.5-flash"
  },
  "error": null,
  "request_id": "req_8df02bc9"
}
```

### 3. Trigger Autonomous Evaluation
```http
POST /api/v1/evaluate/run
Content-Type: application/json

{
  "pipeline_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "dataset_id": "golden_standard_v1"
}
```

---

## 🧪 Quality Testing & Code Standards

Run the complete test suite and code quality linters:

```bash
cd backend

# Execute unit and integration tests
uv run pytest tests/unit

# Execute adversarial anchor tests (hard deployment gate)
uv run pytest tests/adversarial

# Code style and formatting checks
uv run ruff check .
uv run ruff format --check .
```

---

## 📁 Repository Structure

```
AutoRAG/
├── .github/workflows/          # Enterprise CI/CD pipeline definitions
├── docs/                       # 📐 Authoritative architecture & specifications
│   ├── AutoRAG_BRD_v1_0.md     # Business Requirements Document
│   ├── AutoRAG_PRD_v2_4.md     # Product Requirements Document
│   ├── AutoRAG-HLD-v1.0.md     # High-Level Architecture Design
│   ├── AutoRAG-LLD-v1.0.md     # Low-Level Implementation Design
│   └── comprehensive_system_guide.md # Operator and Deployment Manual
├── backend/                    # FastAPI + Celery + LangGraph
│   ├── alembic/                # Database migrations & PostgreSQL RRF functions
│   ├── app/
│   │   ├── chunkers/           # Semantic & hierarchical chunking
│   │   ├── graph/              # LangGraph self-improving workflow
│   │   ├── parsers/            # Multi-format document parser engine
│   │   ├── repositories/       # High-speed asyncpg & Supabase CRUD
│   │   ├── retrieval/          # Hybrid search, Cohere reranking, HyDE
│   │   ├── routes/             # REST endpoints (Ingest, Query, Eval, Deploy)
│   │   ├── services/           # LLM gateways, PII masking, evaluation
│   │   └── workers/            # Distributed Celery tasks & sync connectors
│   └── tests/                  # Unit, integration, & adversarial suites
├── frontend/                   # Next.js 15 Enterprise Console
│   ├── src/app/                # App router (Dashboard, Documents, Pipelines)
│   └── src/components/         # Reusable UI system (Tailwind + Radix)
├── production_widget.html      # Lightweight client web embed widget
├── start_local.ps1             # Local development orchestrator (No Docker)
├── stop_local.ps1              # Process cleanup script
├── Makefile                    # Developer workflow automation
└── docker-compose.yml          # Containerized deployment spec
```

---

## 📐 Authoritative Specifications & Documentation

Comprehensive system specifications are maintained in the [`docs/`](./docs) folder:
* [**Business Requirements (BRD)**](./docs/AutoRAG_BRD_v1_0.md) — Business context, objectives, and ROI criteria.
* [**Product Requirements (PRD)**](./docs/AutoRAG_PRD_v2_4.md) — Feature specifications, user personas, and KPIs.
* [**High-Level Design (HLD)**](./docs/AutoRAG-HLD-v1.0.md) — Data flow, subsystem contracts, and topology.
* [**Low-Level Design (LLD)**](./docs/AutoRAG-LLD-v1.0.md) — Complete database schemas, algorithms, and class diagrams.
* [**Operator System Guide**](./docs/comprehensive_system_guide.md) — Operational runbook and troubleshooting.

---

## 🔒 Security & Privacy

* **Zero Secret Commitment**: All API tokens, service role keys, and credentials are strictly isolated in `.env` files (enforced by `.gitignore`).
* **In-Flight Anonymization**: PII is scrubbed before any document chunk is dispatched to embedding or LLM providers.
* **Audit Trail**: Every query, generation, evaluation score, and configuration promotion is persistently recorded in the audit repository.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
