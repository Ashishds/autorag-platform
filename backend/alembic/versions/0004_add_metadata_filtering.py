"""add metadata filtering — JSONB metadata column + GIN index + updated RRF search function

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-31
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


UP_SQL = """
-- 1. Add metadata JSONB column to chunk_embeddings
ALTER TABLE chunk_embeddings ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb NOT NULL;

-- 2. Create GIN index on metadata column for fast lookups
CREATE INDEX idx_chunk_embeddings_metadata ON chunk_embeddings USING gin (metadata);

-- 3. Drop the old hybrid_search_rrf function
DROP FUNCTION IF EXISTS hybrid_search_rrf(TEXT, vector, UUID, INT, INT);

-- 4. Create the new hybrid_search_rrf function with metadata filtering
CREATE OR REPLACE FUNCTION hybrid_search_rrf(
    query_text      TEXT,
    query_emb       vector(768),
    pipeline_uuid   UUID,
    match_limit     INT DEFAULT 20,
    k               INT DEFAULT 60,
    metadata_filter JSONB DEFAULT NULL
)
RETURNS TABLE (chunk_id UUID, content TEXT, rrf_score NUMERIC)
LANGUAGE sql STABLE AS $$
  WITH dense AS (
    SELECT id,
           ROW_NUMBER() OVER (ORDER BY embedding <=> query_emb) AS rnk
    FROM chunk_embeddings
    WHERE pipeline_id = pipeline_uuid
      AND (metadata_filter IS NULL OR metadata @> metadata_filter)
    ORDER BY embedding <=> query_emb
    LIMIT match_limit * 2
  ),
  keyword AS (
    SELECT id,
           ROW_NUMBER() OVER (
             ORDER BY ts_rank(tsv, plainto_tsquery('english', query_text)) DESC
           ) AS rnk
    FROM chunk_embeddings
    WHERE pipeline_id = pipeline_uuid
      AND tsv @@ plainto_tsquery('english', query_text)
      AND (metadata_filter IS NULL OR metadata @> metadata_filter)
    ORDER BY ts_rank(tsv, plainto_tsquery('english', query_text)) DESC
    LIMIT match_limit * 2
  ),
  fused AS (
    SELECT COALESCE(d.id, kw.id) AS id,
           COALESCE(1.0 / (k + d.rnk), 0) + COALESCE(1.0 / (k + kw.rnk), 0) AS score
    FROM dense d
    FULL OUTER JOIN keyword kw ON d.id = kw.id
  )
  SELECT c.id, c.content, f.score::NUMERIC AS rrf_score
  FROM fused f
  JOIN chunk_embeddings c ON c.id = f.id
  ORDER BY f.score DESC
  LIMIT match_limit;
$$;
"""

DOWN_SQL = """
-- Drop the new function
DROP FUNCTION IF EXISTS hybrid_search_rrf(TEXT, vector, UUID, INT, INT, JSONB);

-- Recreate the old function
CREATE OR REPLACE FUNCTION hybrid_search_rrf(
    query_text    TEXT,
    query_emb     vector(768),
    pipeline_uuid UUID,
    match_limit   INT DEFAULT 20,
    k             INT DEFAULT 60
)
RETURNS TABLE (chunk_id UUID, content TEXT, rrf_score NUMERIC)
LANGUAGE sql STABLE AS $$
  WITH dense AS (
    SELECT id,
           ROW_NUMBER() OVER (ORDER BY embedding <=> query_emb) AS rnk
    FROM chunk_embeddings
    WHERE pipeline_id = pipeline_uuid
    ORDER BY embedding <=> query_emb
    LIMIT match_limit * 2
  ),
  keyword AS (
    SELECT id,
           ROW_NUMBER() OVER (
             ORDER BY ts_rank(tsv, plainto_tsquery('english', query_text)) DESC
           ) AS rnk
    FROM chunk_embeddings
    WHERE pipeline_id = pipeline_uuid
      AND tsv @@ plainto_tsquery('english', query_text)
    ORDER BY ts_rank(tsv, plainto_tsquery('english', query_text)) DESC
    LIMIT match_limit * 2
  ),
  fused AS (
    SELECT COALESCE(d.id, kw.id) AS id,
           COALESCE(1.0 / (k + d.rnk), 0) + COALESCE(1.0 / (k + kw.rnk), 0) AS score
    FROM dense d
    FULL OUTER JOIN keyword kw ON d.id = kw.id
  )
  SELECT c.id, c.content, f.score::NUMERIC AS rrf_score
  FROM fused f
  JOIN chunk_embeddings c ON c.id = f.id
  ORDER BY f.score DESC
  LIMIT match_limit;
$$;

-- Drop GIN index and metadata column
DROP INDEX IF EXISTS idx_chunk_embeddings_metadata;
ALTER TABLE chunk_embeddings DROP COLUMN IF EXISTS metadata;
"""


def upgrade() -> None:
    op.execute(UP_SQL)


def downgrade() -> None:
    op.execute(DOWN_SQL)
