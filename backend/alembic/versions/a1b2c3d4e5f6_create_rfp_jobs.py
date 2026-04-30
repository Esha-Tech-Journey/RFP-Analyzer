"""create normalized schema

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. rfp_documents — lightweight document metadata
    op.create_table(
        "rfp_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. rfp_document_content — extracted text stored separately
    op.create_table(
        "rfp_document_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["rfp_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(
        "ix_rfp_document_content_document_id",
        "rfp_document_content",
        ["document_id"],
    )

    # 3. rfp_jobs — one analysis run per document
    op.create_table(
        "rfp_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="jobstatus"),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(10), nullable=True),
        sa.Column("effort", sa.String(10), nullable=True),
        sa.Column("recommendation", sa.String(20), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("requirements", sa.JSON(), nullable=True),
        sa.Column("risk_reasons", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"], ["rfp_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rfp_jobs_document_id", "rfp_jobs", ["document_id"])
    op.create_index("ix_rfp_jobs_risk_level", "rfp_jobs", ["risk_level"])
    op.create_index("ix_rfp_jobs_effort", "rfp_jobs", ["effort"])
    op.create_index("ix_rfp_jobs_recommendation", "rfp_jobs", ["recommendation"])


def downgrade() -> None:
    op.drop_table("rfp_jobs")
    op.drop_table("rfp_document_content")
    op.drop_table("rfp_documents")
    sa.Enum(name="jobstatus").drop(op.get_bind())
