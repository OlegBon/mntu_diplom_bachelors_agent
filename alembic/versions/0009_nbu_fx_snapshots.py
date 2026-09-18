"""Freeze an official NBU USD/UAH rate with market-reference valuations.

Revision ID: 0009_nbu_fx_snapshots
Revises: 0008_market_data_providers
Create Date: 2026-09-17

The migration intentionally does not alter legacy report prices or historical
market references. New references receive an immutable FX snapshot at attach
time; the stored UAH total does not float with later NBU publications.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_nbu_fx_snapshots"
down_revision: Union[str, Sequence[str], None] = "0008_market_data_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    providers = sa.table(
        "market_data_providers",
        sa.column("provider_code", sa.String), sa.column("display_name", sa.String),
        sa.column("provider_type", sa.String), sa.column("documentation_url", sa.String),
        sa.column("terms_url", sa.String), sa.column("scope_note", sa.Text),
        sa.column("is_active", sa.Boolean), schema="diamond_market",
    )
    op.bulk_insert(providers, [{
        "provider_code": "nbu", "display_name": "НБУ", "provider_type": "fx_reference",
        "documentation_url": "https://bank.gov.ua/ua/markets/exchangerates",
        "terms_url": "https://bank.gov.ua/ua/about/terms-of-use",
        "scope_note": "Офіційний курс USD/UAH. Під час прикріплення орієнтира курс фіксується у звіті.",
        "is_active": True,
    }])
    op.create_table(
        "fx_data_snapshots",
        sa.Column("fx_snapshot_id", sa.Integer(), primary_key=True),
        sa.Column("provider_code", sa.String(length=32), nullable=False),
        sa.Column("base_currency_code", sa.String(length=3), nullable=False),
        sa.Column("quote_currency_code", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        schema="diamond_market",
    )
    op.create_index("ix_diamond_market_fx_data_snapshots_fx_snapshot_id", "fx_data_snapshots", ["fx_snapshot_id"], schema="diamond_market")
    op.create_index("ix_diamond_market_fx_data_snapshots_provider_code", "fx_data_snapshots", ["provider_code"], schema="diamond_market")
    for column in (
        sa.Column("fx_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("fx_rate", sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column("fx_rate_date", sa.Date(), nullable=True),
        sa.Column("converted_amount", sa.DECIMAL(precision=14, scale=2), nullable=True),
        sa.Column("converted_currency_code", sa.String(length=3), nullable=True),
    ):
        op.add_column("stone_valuations", column, schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_stone_valuations_fx_snapshot_id", "stone_valuations", ["fx_snapshot_id"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_diamond_oltp_stone_valuations_fx_snapshot_id", table_name="stone_valuations", schema="diamond_oltp")
    for name in ("converted_currency_code", "converted_amount", "fx_rate_date", "fx_rate", "fx_snapshot_id"):
        op.drop_column("stone_valuations", name, schema="diamond_oltp")
    op.drop_index("ix_diamond_market_fx_data_snapshots_provider_code", table_name="fx_data_snapshots", schema="diamond_market")
    op.drop_index("ix_diamond_market_fx_data_snapshots_fx_snapshot_id", table_name="fx_data_snapshots", schema="diamond_market")
    op.drop_table("fx_data_snapshots", schema="diamond_market")
    op.execute("DELETE FROM diamond_market.market_data_providers WHERE provider_code = 'nbu'")
