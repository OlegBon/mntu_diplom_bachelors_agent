"""Record server-timed expert work sessions for saved draft reports.

Revision ID: 0011_expert_work_sessions
Revises: 0010_market_reference_policy
Create Date: 2026-09-22

This revision adds empty operational tables only. It does not infer or backfill
active time from historical report timestamps, report events, or legacy
``evaluation_time_sec`` values.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_expert_work_sessions"
down_revision: Union[str, Sequence[str], None] = "0010_market_reference_policy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_work_sessions",
        sa.Column("work_session_id", sa.String(length=36), primary_key=True),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("tab_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("active_seconds", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("end_reason", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["expert_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_report_work_sessions_report_id", "report_work_sessions", ["report_id"], schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_report_work_sessions_expert_id", "report_work_sessions", ["expert_id"], schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_report_work_sessions_ended_at", "report_work_sessions", ["ended_at"], schema="diamond_oltp")
    op.create_table(
        "report_work_session_events",
        sa.Column("work_session_event_id", sa.Integer(), primary_key=True),
        sa.Column("work_session_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("active_seconds", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["work_session_id"], ["diamond_oltp.report_work_sessions.work_session_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_report_work_session_events_work_session_id", "report_work_session_events", ["work_session_id"], schema="diamond_oltp")
    op.create_table(
        "report_work_session_leases",
        sa.Column("report_id", sa.String(length=20), primary_key=True),
        sa.Column("expert_id", sa.Integer(), primary_key=True),
        sa.Column("work_session_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("tab_id", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["expert_id"], ["diamond_oltp.experts.expert_id"]),
        sa.ForeignKeyConstraint(["work_session_id"], ["diamond_oltp.report_work_sessions.work_session_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_report_work_session_leases_expires_at", "report_work_session_leases", ["expires_at"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_diamond_oltp_report_work_session_leases_expires_at", table_name="report_work_session_leases", schema="diamond_oltp")
    op.drop_table("report_work_session_leases", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_work_session_events_work_session_id", table_name="report_work_session_events", schema="diamond_oltp")
    op.drop_table("report_work_session_events", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_work_sessions_ended_at", table_name="report_work_sessions", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_work_sessions_expert_id", table_name="report_work_sessions", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_work_sessions_report_id", table_name="report_work_sessions", schema="diamond_oltp")
    op.drop_table("report_work_sessions", schema="diamond_oltp")
