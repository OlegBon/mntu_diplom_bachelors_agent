"""Store isolated synthetic actors and workflow events for demo analytics.

Revision ID: 0016_demo_synthetic_workflow
Revises: 0015_multi_provider_market_references
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0016_demo_synthetic_workflow"
down_revision: Union[str, Sequence[str], None] = "0015_multi_provider_market_references"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demo_synthetic_actors",
        sa.Column("actor_id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("actor_key", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["diamond_oltp.demo_datasets.dataset_id"]),
        sa.UniqueConstraint("dataset_id", "actor_key", name="uq_demo_actor_dataset_key"),
        schema="diamond_oltp",
    )
    op.create_index("ix_demo_synthetic_actors_dataset_id", "demo_synthetic_actors", ["dataset_id"], schema="diamond_oltp")
    op.create_table(
        "demo_workflow_events",
        sa.Column("workflow_event_id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=16), nullable=True),
        sa.Column("to_status", sa.String(length=16), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["diamond_oltp.demo_datasets.dataset_id"]),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["diamond_oltp.demo_synthetic_actors.actor_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_demo_workflow_dataset_occurred", "demo_workflow_events", ["dataset_id", "occurred_at"], schema="diamond_oltp")
    op.create_index("ix_demo_workflow_events_report_id", "demo_workflow_events", ["report_id"], schema="diamond_oltp")
    op.create_index("ix_demo_workflow_events_actor_id", "demo_workflow_events", ["actor_id"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_table("demo_workflow_events", schema="diamond_oltp")
    op.drop_table("demo_synthetic_actors", schema="diamond_oltp")
