"""add document pipeline enhancements — mime_type, source_type, media_path

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-30
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


UP_SQL = """
ALTER TABLE documents ADD COLUMN mime_type VARCHAR(100);

ALTER TABLE chunk_embeddings ADD COLUMN source_type VARCHAR(50) DEFAULT 'text'
  CHECK (source_type IN ('text', 'table', 'figure', 'image'));

ALTER TABLE chunk_embeddings ADD COLUMN media_path VARCHAR(512);
"""

DOWN_SQL = """
ALTER TABLE chunk_embeddings DROP COLUMN IF EXISTS media_path;
ALTER TABLE chunk_embeddings DROP COLUMN IF EXISTS source_type;
ALTER TABLE documents DROP COLUMN IF EXISTS mime_type;
"""


def upgrade() -> None:
    op.execute(UP_SQL)


def downgrade() -> None:
    op.execute(DOWN_SQL)
