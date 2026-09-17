"""Configure providers used for future system market references.

Revision ID: 0010_market_reference_policy
Revises: 0009_nbu_fx_snapshots
Create Date: 2026-09-17

The single policy row selects a market provider and optionally an FX provider
only for future automatic valuations. Historical StoneValuation provenance is
already frozen and is intentionally not backfilled or changed.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_market_reference_policy"
down_revision: Union[str, Sequence[str], None] = "0009_nbu_fx_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_reference_policies",
        sa.Column("policy_id", sa.Integer(), primary_key=True),
        sa.Column("market_provider_code", sa.String(length=32), nullable=True),
        sa.Column("use_fx_conversion", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("fx_provider_code", sa.String(length=32), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["market_provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        sa.ForeignKeyConstraint(["fx_provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        sa.CheckConstraint("policy_id = 1", name="ck_market_reference_policy_singleton"),
        schema="diamond_market",
    )
    policy = sa.table(
        "market_reference_policies",
        sa.column("policy_id", sa.Integer),
        sa.column("market_provider_code", sa.String),
        sa.column("use_fx_conversion", sa.Boolean),
        sa.column("fx_provider_code", sa.String),
        schema="diamond_market",
    )
    op.bulk_insert(policy, [{
        "policy_id": 1,
        "market_provider_code": "openfacet",
        "use_fx_conversion": True,
        "fx_provider_code": "nbu",
    }])


def downgrade() -> None:
    op.drop_table("market_reference_policies", schema="diamond_market")
