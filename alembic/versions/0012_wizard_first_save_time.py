"""Record server-timed elapsed preparation before a report's first save.

Revision ID: 0012_wizard_first_save_time
Revises: 0011_expert_work_sessions
Create Date: 2026-09-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0012_wizard_first_save_time"
down_revision: Union[str, Sequence[str], None] = "0011_expert_work_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("diamond_reports", sa.Column("first_save_started_at", sa.DateTime(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("time_to_first_save_seconds", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.create_table(
        "wizard_work_sessions",
        sa.Column("wizard_session_id", sa.String(length=36), primary_key=True),
        sa.Column("expert_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("tab_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["expert_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_wizard_work_sessions_expires_at", "wizard_work_sessions", ["expires_at"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_diamond_oltp_wizard_work_sessions_expires_at", table_name="wizard_work_sessions", schema="diamond_oltp")
    op.drop_table("wizard_work_sessions", schema="diamond_oltp")
    op.drop_column("diamond_reports", "time_to_first_save_seconds", schema="diamond_oltp")
    op.drop_column("diamond_reports", "first_save_started_at", schema="diamond_oltp")
