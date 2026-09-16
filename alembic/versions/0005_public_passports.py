"""Add revocable public passport tokens for issued reports.

Revision ID: 0005_public_passports
Revises: 0004_report_wizard
Create Date: 2026-09-16

The table stores only publication tokens and audit timestamps. It does not
backfill or expose historical reports, media, prices, or expert identities.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_public_passports"
down_revision: Union[str, Sequence[str], None] = "0004_report_wizard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_passports",
        sa.Column("passport_id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["diamond_oltp.experts.expert_id"]),
        sa.PrimaryKeyConstraint("passport_id"),
        sa.UniqueConstraint("public_id", name="uq_public_passports_public_id"),
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_oltp_public_passports_report_id",
        "public_passports",
        ["report_id"],
        unique=False,
        schema="diamond_oltp",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diamond_oltp_public_passports_report_id",
        table_name="public_passports",
        schema="diamond_oltp",
    )
    op.drop_table("public_passports", schema="diamond_oltp")
