"""Converge demo workflow indexes with the SQLAlchemy model.

Revision ID: 0017_demo_workflow_index_convergence
Revises: 0016_demo_synthetic_workflow
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0017_demo_workflow_index_convergence"
down_revision: Union[str, Sequence[str], None] = "0016_demo_synthetic_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_demo_workflow_events_dataset_id", "demo_workflow_events", ["dataset_id"], schema="diamond_oltp")
    op.create_index("ix_demo_workflow_events_occurred_at", "demo_workflow_events", ["occurred_at"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_demo_workflow_events_occurred_at", table_name="demo_workflow_events", schema="diamond_oltp")
    op.drop_index("ix_demo_workflow_events_dataset_id", table_name="demo_workflow_events", schema="diamond_oltp")
