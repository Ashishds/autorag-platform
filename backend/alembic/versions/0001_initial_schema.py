"""initial schema — core tables (LLD §3)

Revision ID: 0001
Revises:
Create Date: 2026-05-29
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- UUIDv7-ish helper for the boilerplate. Replace with a real v7 impl in production.
CREATE OR REPLACE FUNCTION uuid_generate_v7() RETURNS uuid
LANGUAGE sql VOLATILE AS $$ SELECT gen_random_uuid() $$;

CREATE TABLE pipelines (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id   UUID NOT NULL,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    config            JSONB NOT NULL,
    chunking_strategy VARCHAR(50) NOT NULL
                      CHECK (chunking_strategy IN ('semantic','hierarchical','auto')),
    retrieval_method  VARCHAR(50) NOT NULL DEFAULT 'hybrid'
                      CHECK (retrieval_method IN ('dense','hybrid','hybrid_hyde')),
    llm_judge         VARCHAR(50) NOT NULL DEFAULT 'gemini-2.5-pro',
    approval_mode     VARCHAR(50) NOT NULL DEFAULT 'human_in_loop'
                      CHECK (approval_mode IN ('auto','human_in_loop','mandatory_gate')),
    active_version    UUID,
    status            VARCHAR(30) NOT NULL DEFAULT 'draft'
                      CHECK (status IN ('draft','active','archived')),
    created_by        UUID NOT NULL,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_pipelines_org ON pipelines(organization_id);
CREATE INDEX idx_pipelines_status ON pipelines(status);

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL,
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id),
    filename        VARCHAR(255) NOT NULL,
    file_size       BIGINT NOT NULL,
    storage_path    VARCHAR(512) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued','pre_processing','processing','completed','failed','cancelled')),
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    pii_entities    INTEGER NOT NULL DEFAULT 0,
    pii_tier2_run   BOOLEAN NOT NULL DEFAULT FALSE,
    error           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_documents_pipeline ON documents(pipeline_id);
CREATE INDEX idx_documents_org ON documents(organization_id);
CREATE INDEX idx_documents_status ON documents(status);

CREATE TABLE chunk_embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    chunk_index     INTEGER NOT NULL,
    token_count     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(768) NOT NULL,
    tsv             tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    page_number     INTEGER,
    chunk_strategy  VARCHAR(50) NOT NULL
                    CHECK (chunk_strategy IN ('semantic','hierarchical_parent','hierarchical_child')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_chunks_doc ON chunk_embeddings (document_id);
CREATE INDEX idx_chunks_pipeline ON chunk_embeddings (pipeline_id);

CREATE TABLE pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id),
    organization_id UUID NOT NULL,
    trace_id        UUID NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','running','completed','failed','cancelled')),
    triggered_by    VARCHAR(50) NOT NULL
                    CHECK (triggered_by IN ('api','observer','scheduler')),
    prompt_versions JSONB,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    error_message   TEXT,
    metadata        JSONB,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_runs_pipeline ON pipeline_runs(pipeline_id);
CREATE INDEX idx_runs_status ON pipeline_runs(status);

CREATE TABLE golden_datasets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id),
    organization_id UUID NOT NULL,
    question        TEXT NOT NULL,
    expected_answer TEXT,
    expected_chunks UUID[],
    question_type   VARCHAR(30) NOT NULL DEFAULT 'synthetic'
                    CHECK (question_type IN ('synthetic','adversarial_fixed','adversarial_dynamic','human')),
    human_score     NUMERIC(5,4),
    set_version     INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_golden_pipeline ON golden_datasets(pipeline_id);
CREATE INDEX idx_golden_type ON golden_datasets(question_type);

CREATE TABLE evaluations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    run_id              UUID NOT NULL REFERENCES pipeline_runs(id),
    organization_id     UUID NOT NULL,
    golden_set_id       UUID NOT NULL,
    unified_score       NUMERIC(5,4) NOT NULL,
    retrieval_score     NUMERIC(5,4) NOT NULL,
    quality_score       NUMERIC(5,4) NOT NULL,
    faithfulness_score  NUMERIC(5,4) NOT NULL,
    latency_penalty     NUMERIC(5,4) NOT NULL DEFAULT 0,
    cost_penalty        NUMERIC(5,4) NOT NULL DEFAULT 0,
    ragas_context_precision   NUMERIC(5,4),
    ragas_context_recall      NUMERIC(5,4),
    ragas_answer_faithfulness NUMERIC(5,4),
    ragas_answer_relevancy    NUMERIC(5,4),
    ragas_scorer        VARCHAR(50),
    adversarial_pass_rate     NUMERIC(5,4),
    adversarial_fail_count    INTEGER DEFAULT 0,
    adversarial_dynamic_count INTEGER DEFAULT 5,
    deploy_eligible     BOOLEAN NOT NULL DEFAULT FALSE,
    failure_reason      TEXT,
    judge_reasoning     TEXT,
    eval_duration_ms    INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_eval_run ON evaluations(run_id);
CREATE INDEX idx_eval_score ON evaluations(unified_score);

CREATE TABLE experiments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    run_id          UUID NOT NULL REFERENCES pipeline_runs(id),
    organization_id UUID NOT NULL,
    parent_run_id   UUID REFERENCES pipeline_runs(id),
    golden_set_id   UUID NOT NULL,
    variant_config  JSONB NOT NULL,
    score_delta     NUMERIC(6,4),
    improvement_type VARCHAR(50),
    approval_tier   VARCHAR(30)
                    CHECK (approval_tier IN ('auto','human_in_loop','mandatory_gate')),
    approval_status VARCHAR(30) DEFAULT 'pending'
                    CHECK (approval_status IN ('pending','approved','rejected')),
    approved_by     UUID,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_experiments_run ON experiments(run_id);

CREATE TABLE deployments (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    pipeline_id         UUID NOT NULL REFERENCES pipelines(id),
    run_id              UUID NOT NULL REFERENCES pipeline_runs(id),
    organization_id     UUID NOT NULL,
    config_snapshot     JSONB NOT NULL,
    previous_deployment UUID REFERENCES deployments(id),
    environment         VARCHAR(20) NOT NULL DEFAULT 'production'
                        CHECK (environment IN ('staging','production')),
    strategy            VARCHAR(20) NOT NULL DEFAULT 'config_activation',
    status              VARCHAR(30) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','rolled_back','superseded')),
    unified_score       NUMERIC(5,4) NOT NULL,
    activated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rolled_back_at      TIMESTAMP WITH TIME ZONE,
    rollback_reason     TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_deploy_pipeline ON deployments(pipeline_id);
CREATE INDEX idx_deploy_status ON deployments(status);

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL,
    event_type      VARCHAR(50) NOT NULL CHECK (event_type IN (
                        'PIPELINE_CREATED','PIPELINE_UPDATED',
                        'INGESTION_STARTED','INGESTION_COMPLETED',
                        'DOCUMENT_STATUS_CHANGED',
                        'EVALUATION_STARTED','EVALUATION_COMPLETED',
                        'IMPROVEMENT_TRIGGERED',
                        'APPROVAL_GRANTED','APPROVAL_DENIED',
                        'PIPELINE_DEPLOYED','PIPELINE_ROLLED_BACK'
                    )),
    actor_id        UUID NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID NOT NULL,
    trace_id        UUID NOT NULL,
    payload         JSONB,
    ip_address      INET,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_audit_org ON audit_log(organization_id);
CREATE INDEX idx_audit_event ON audit_log(event_type);
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;

CREATE TABLE query_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id),
    organization_id UUID NOT NULL,
    trace_id        UUID NOT NULL,
    query_hash      VARCHAR(64) NOT NULL,
    rewrite_applied BOOLEAN NOT NULL DEFAULT FALSE,
    hyde_applied    BOOLEAN NOT NULL DEFAULT FALSE,
    compression_applied BOOLEAN NOT NULL DEFAULT FALSE,
    retrieval_k     INTEGER NOT NULL,
    chunks_retrieved INTEGER NOT NULL,
    rerank_applied  BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms      INTEGER NOT NULL,
    token_count     INTEGER,
    llm_provider    VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_qlogs_pipeline ON query_logs(pipeline_id);
CREATE INDEX idx_qlogs_latency ON query_logs(latency_ms);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS query_logs CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS deployments CASCADE;
DROP TABLE IF EXISTS experiments CASCADE;
DROP TABLE IF EXISTS evaluations CASCADE;
DROP TABLE IF EXISTS golden_datasets CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS chunk_embeddings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS pipelines CASCADE;
"""


def upgrade() -> None:
    op.execute(SCHEMA_SQL)


def downgrade() -> None:
    op.execute(DOWN_SQL)
