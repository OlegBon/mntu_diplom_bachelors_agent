"""Add private report media metadata without inventing legacy attachments.

Revision ID: 0003_media_assets
Revises: 0002_report_core
Create Date: 2026-09-15

Only metadata is migrated. Legacy plotting_image and real_image columns contain
unverified placeholder paths, so this revision deliberately creates no media
records for them.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_media_assets"
down_revision: Union[str, Sequence[str], None] = "0002_report_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("media_id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_media_assets_media_id", "media_assets", ["media_id"], schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_media_assets_report_id", "media_assets", ["report_id"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_diamond_oltp_media_assets_report_id", table_name="media_assets", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_media_assets_media_id", table_name="media_assets", schema="diamond_oltp")
    op.drop_table("media_assets", schema="diamond_oltp")
