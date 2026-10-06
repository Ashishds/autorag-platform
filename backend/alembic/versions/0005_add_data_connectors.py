"""add data_connectors table and update documents table

Revision ID: 0005_add_data_connectors
Revises: 0004_add_metadata_filtering
Create Date: 2026-05-31 17:39:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '0005_add_data_connectors'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create data_connectors table
    op.execute("""
    CREATE TABLE data_connectors (
        id UUID PRIMARY KEY,
        organization_id UUID NOT NULL,
        pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL,
        config JSONB NOT NULL,
        status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
        last_synced_at TIMESTAMP WITH TIME ZONE,
        sync_interval_minutes INT DEFAULT 60,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)

    # 2. Add columns to documents table
    op.execute("""
    ALTER TABLE documents 
    ADD COLUMN connector_id UUID REFERENCES data_connectors(id) ON DELETE CASCADE,
    ADD COLUMN source_id VARCHAR(255);
    """)

    # 3. Create index for faster sync queries
    op.execute("""
    CREATE INDEX ix_documents_connector_id ON documents (connector_id);
    """)

def downgrade() -> None:
    # 1. Drop index and columns from documents
    op.execute("""
    DROP INDEX IF EXISTS ix_documents_connector_id;
    ALTER TABLE documents 
    DROP COLUMN IF EXISTS connector_id,
    DROP COLUMN IF EXISTS source_id;
    """)

    # 2. Drop data_connectors table
    op.execute("DROP TABLE IF EXISTS data_connectors;")
