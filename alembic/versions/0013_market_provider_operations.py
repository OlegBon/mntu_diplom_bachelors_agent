"""Add provider schedules and immutable operation outcomes.

Revision ID: 0013_market_provider_operations
Revises: 0012_wizard_first_save_time
Create Date: 2026-09-23

The revision is future-only: it creates operational configuration and logs but
does not rewrite any market/FX snapshot, valuation or report event.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_market_provider_operations"
down_revision: Union[str, Sequence[str], None] = "0012_wizard_first_save_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "market_data_snapshots", "created_by_id", existing_type=sa.Integer(), nullable=True,
        schema="diamond_market",
    )
    op.create_table(
        "market_provider_schedules",
        sa.Column("provider_code", sa.String(length=32), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("timezone_name", sa.String(length=64), nullable=False, server_default="Europe/Kyiv"),
        sa.Column("scheduled_hour", sa.Integer(), nullable=False),
        sa.Column("scheduled_minute", sa.Integer(), nullable=False),
        sa.Column("warn_after_hours", sa.Integer(), nullable=False),
        sa.Column("block_after_hours", sa.Integer(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        schema="diamond_market",
    )
    op.create_table(
        "market_provider_operations",
        sa.Column("operation_id", sa.Integer(), primary_key=True),
        sa.Column("provider_code", sa.String(length=32), nullable=False),
        sa.Column("trigger_type", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("market_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("fx_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("initiated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        schema="diamond_market",
    )
    op.create_index("ix_market_operation_provider_started", "market_provider_operations", ["provider_code", "started_at"], schema="diamond_market")
    schedules = sa.table(
        "market_provider_schedules",
        sa.column("provider_code", sa.String), sa.column("enabled", sa.Boolean),
        sa.column("timezone_name", sa.String), sa.column("scheduled_hour", sa.Integer),
        sa.column("scheduled_minute", sa.Integer), sa.column("warn_after_hours", sa.Integer),
        sa.column("block_after_hours", sa.Integer), schema="diamond_market",
    )
    op.bulk_insert(schedules, [
        {"provider_code": "openfacet", "enabled": True, "timezone_name": "Europe/Kyiv", "scheduled_hour": 8, "scheduled_minute": 30, "warn_after_hours": 24 * 7, "block_after_hours": 24 * 14},
        {"provider_code": "nbu", "enabled": True, "timezone_name": "Europe/Kyiv", "scheduled_hour": 15, "scheduled_minute": 40, "warn_after_hours": 36, "block_after_hours": 72},
    ])


def downgrade() -> None:
    op.drop_index("ix_market_operation_provider_started", table_name="market_provider_operations", schema="diamond_market")
    op.drop_table("market_provider_operations", schema="diamond_market")
    op.drop_table("market_provider_schedules", schema="diamond_market")
    op.alter_column(
        "market_data_snapshots", "created_by_id", existing_type=sa.Integer(), nullable=False,
        schema="diamond_market",
    )
