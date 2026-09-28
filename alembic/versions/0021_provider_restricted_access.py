"""Add provider-neutral restricted-access governance.

Revision ID: 0021_provider_restricted_access
Revises: 0020_demo_provider_analytics_eligibility
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0021_provider_restricted_access"
down_revision: Union[str, Sequence[str], None] = "0020_demo_provider_analytics_eligibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("experts", sa.Column("partner_controls_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")), schema="diamond_oltp")
    op.create_table(
        "market_provider_access_policies",
        sa.Column("provider_code", sa.String(length=32), sa.ForeignKey("diamond_market.market_data_providers.provider_code"), primary_key=True),
        sa.Column("access_mode", sa.String(length=32), nullable=False, server_default="standard_internal"),
        sa.Column("trial_expires_at", sa.DateTime(), nullable=True),
        sa.Column("daily_request_limit", sa.Integer(), nullable=True),
        sa.Column("natural_only", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("internal_only", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("public_display_allowed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("ml_allowed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("terms_reference", sa.Text(), nullable=True), sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), schema="diamond_market",
    )
    op.create_table(
        "market_provider_access_assignments",
        sa.Column("assignment_id", sa.Integer(), primary_key=True),
        sa.Column("provider_code", sa.String(length=32), sa.ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=False),
        sa.Column("expert_id", sa.Integer(), sa.ForeignKey("diamond_oltp.experts.expert_id"), nullable=False),
        sa.Column("granted_by_id", sa.Integer(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("provider_code", "expert_id", name="uq_market_provider_access_assignment"), schema="diamond_market",
    )
    op.create_table(
        "market_provider_access_events",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("provider_code", sa.String(length=32), sa.ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False), sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("subject_expert_id", sa.Integer(), nullable=True), sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("state_json", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), schema="diamond_market",
    )
    op.create_index("ix_market_provider_access_events_provider_code", "market_provider_access_events", ["provider_code"], schema="diamond_market")
    op.create_index("ix_market_provider_access_events_created_at", "market_provider_access_events", ["created_at"], schema="diamond_market")
    op.execute("INSERT INTO diamond_market.market_provider_access_policies (provider_code) SELECT provider_code FROM diamond_market.market_data_providers")


def downgrade() -> None:
    op.drop_index("ix_market_provider_access_events_created_at", table_name="market_provider_access_events", schema="diamond_market")
    op.drop_index("ix_market_provider_access_events_provider_code", table_name="market_provider_access_events", schema="diamond_market")
    op.drop_table("market_provider_access_events", schema="diamond_market")
    op.drop_table("market_provider_access_assignments", schema="diamond_market")
    op.drop_table("market_provider_access_policies", schema="diamond_market")
    op.drop_column("experts", "partner_controls_enabled", schema="diamond_oltp")
