"""Normalize future market-reference policy providers.

Revision ID: 0015_multi_provider_market_references
Revises: 0014_demo_dataset_isolation
Create Date: 2026-09-25

Only the mutable policy configuration is copied to the normalized child table.
Historical snapshots, valuations, events, reports and public projections are
intentionally not rewritten.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0015_multi_provider_market_references"
down_revision: Union[str, Sequence[str], None] = "0014_demo_dataset_isolation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "market_data_providers",
        sa.Column("brand_asset_key", sa.String(length=100), nullable=True),
        schema="diamond_market",
    )
    op.create_table(
        "market_reference_policy_providers",
        sa.Column("policy_provider_id", sa.Integer(), primary_key=True),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.String(length=32), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["policy_id"], ["diamond_market.market_reference_policies.policy_id"]),
        sa.ForeignKeyConstraint(["provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        sa.UniqueConstraint("policy_id", "provider_code", name="uq_market_policy_provider"),
        schema="diamond_market",
    )
    op.execute(
        "INSERT INTO diamond_market.market_reference_policy_providers "
        "(policy_id, provider_code, display_order, updated_by_id) "
        "SELECT policy_id, market_provider_code, 0, updated_by_id "
        "FROM diamond_market.market_reference_policies "
        "WHERE market_provider_code IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_table("market_reference_policy_providers", schema="diamond_market")
    op.drop_column("market_data_providers", "brand_asset_key", schema="diamond_market")
