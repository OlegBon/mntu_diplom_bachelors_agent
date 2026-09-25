"""Add immutable demo dataset manifests and report-scope isolation.

Revision ID: 0014_demo_dataset_isolation
Revises: 0013_market_provider_operations
Create Date: 2026-09-25

This revision is schema-only.  It intentionally does not classify the
historical DR-00001…DR-01000 seed: that backfill requires a read-only
inventory, backup and a separate explicit operator approval.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0014_demo_dataset_isolation"
down_revision: Union[str, Sequence[str], None] = "0013_market_provider_operations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demo_datasets",
        sa.Column("dataset_id", sa.String(length=64), primary_key=True),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("generator_version", sa.String(length=64), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("scope_note", sa.Text(), nullable=False),
        sa.Column("analysis_eligibility", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema="diamond_oltp",
    )
    op.add_column(
        "diamond_reports",
        sa.Column("record_scope", sa.String(length=16), nullable=False, server_default="operational"),
        schema="diamond_oltp",
    )
    op.add_column(
        "diamond_reports",
        sa.Column("demo_dataset_id", sa.String(length=64), nullable=True),
        schema="diamond_oltp",
    )
    op.create_foreign_key(
        "fk_diamond_reports_demo_dataset",
        "diamond_reports",
        "demo_datasets",
        ["demo_dataset_id"],
        ["dataset_id"],
        source_schema="diamond_oltp",
        referent_schema="diamond_oltp",
    )
    op.create_check_constraint(
        "ck_diamond_reports_record_scope",
        "diamond_reports",
        "record_scope IN ('operational', 'demo')",
        schema="diamond_oltp",
    )
    op.create_check_constraint(
        "ck_diamond_reports_scope_dataset",
        "diamond_reports",
        "(record_scope = 'operational' AND demo_dataset_id IS NULL) OR "
        "(record_scope = 'demo' AND demo_dataset_id IS NOT NULL)",
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_reports_scope_report_id",
        "diamond_reports",
        ["record_scope", "report_id"],
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_reports_demo_dataset_id",
        "diamond_reports",
        ["demo_dataset_id"],
        schema="diamond_oltp",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diamond_reports_demo_dataset_id",
        table_name="diamond_reports",
        schema="diamond_oltp",
    )
    op.drop_index(
        "ix_diamond_reports_scope_report_id",
        table_name="diamond_reports",
        schema="diamond_oltp",
    )
    op.drop_constraint(
        "ck_diamond_reports_scope_dataset",
        "diamond_reports",
        type_="check",
        schema="diamond_oltp",
    )
    op.drop_constraint(
        "ck_diamond_reports_record_scope",
        "diamond_reports",
        type_="check",
        schema="diamond_oltp",
    )
    op.drop_constraint(
        "fk_diamond_reports_demo_dataset",
        "diamond_reports",
        type_="foreignkey",
        schema="diamond_oltp",
    )
    op.drop_column("diamond_reports", "demo_dataset_id", schema="diamond_oltp")
    op.drop_column("diamond_reports", "record_scope", schema="diamond_oltp")
    op.drop_table("demo_datasets", schema="diamond_oltp")
