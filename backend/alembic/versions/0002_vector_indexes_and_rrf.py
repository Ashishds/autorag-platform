"""HNSW + GIN indexes and DB-level RRF function (LLD §4)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-29
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


UP_SQL = """
CREATE INDEX idx_chunk_embeddings_cosine ON chunk_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

CREATE INDEX idx_chunk_embeddings_tsv ON chunk_embeddings
USING gin (tsv);

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
"""

DOWN_SQL = """
DROP FUNCTION IF EXISTS hybrid_search_rrf(TEXT, vector, UUID, INT, INT);
DROP INDEX IF EXISTS idx_chunk_embeddings_tsv;
DROP INDEX IF EXISTS idx_chunk_embeddings_cosine;
"""


def upgrade() -> None:
    op.execute(UP_SQL)


def downgrade() -> None:
    op.execute(DOWN_SQL)
