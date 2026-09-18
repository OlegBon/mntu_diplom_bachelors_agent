"""Add provider-neutral market-data snapshots without changing legacy prices.

Revision ID: 0008_market_data_providers
Revises: 0007_grading_rulesets
Create Date: 2026-09-17

The revision registers OpenFacet as a documented market-reference provider but
does not fetch data, create a valuation, modify ``DiamondReport.price`` or
recalculate any historical report. Snapshot imports remain an explicit
administrator action after upgrade.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_market_data_providers"
down_revision: Union[str, Sequence[str], None] = "0007_grading_rulesets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_data_providers",
        sa.Column("provider_code", sa.String(length=32), primary_key=True),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False),
        sa.Column("documentation_url", sa.String(length=255), nullable=False),
        sa.Column("terms_url", sa.String(length=255), nullable=False),
        sa.Column("scope_note", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema="diamond_market",
    )
    providers = sa.table(
        "market_data_providers",
        sa.column("provider_code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("provider_type", sa.String),
        sa.column("documentation_url", sa.String),
        sa.column("terms_url", sa.String),
        sa.column("scope_note", sa.Text),
        sa.column("is_active", sa.Boolean),
        schema="diamond_market",
    )
    op.bulk_insert(
        providers,
        [{
            "provider_code": "openfacet",
            "display_name": "OpenFacet",
            "provider_type": "market_reference",
            "documentation_url": "https://openfacet.net/en/api-docs/",
            "terms_url": "https://openfacet.net/en/terms/",
            "scope_note": (
                "Model-based retail reference for comparable natural GIA-certified stones; "
                "not an appraisal, offer, transaction or sale price."
            ),
            "is_active": True,
        }],
    )
    op.create_table(
        "market_data_snapshots",
        sa.Column("snapshot_id", sa.Integer(), primary_key=True),
        sa.Column("provider_code", sa.String(length=32), nullable=False),
        sa.Column("snapshot_kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="candidate"),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("methodology_url", sa.String(length=255), nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=False),
        sa.Column("quote_count", sa.Integer(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["provider_code"], ["diamond_market.market_data_providers.provider_code"]),
        schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_data_snapshots_snapshot_id",
        "market_data_snapshots", ["snapshot_id"], schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_data_snapshots_provider_code",
        "market_data_snapshots", ["provider_code"], schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_data_snapshots_status",
        "market_data_snapshots", ["status"], schema="diamond_market",
    )
    op.create_table(
        "market_data_quotes",
        sa.Column("quote_id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("shape_code", sa.String(length=32), nullable=False),
        sa.Column("carat_anchor", sa.DECIMAL(precision=8, scale=3), nullable=False),
        sa.Column("color_code", sa.String(length=16), nullable=False),
        sa.Column("clarity_code", sa.String(length=16), nullable=False),
        sa.Column("price_per_carat", sa.DECIMAL(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["diamond_market.market_data_snapshots.snapshot_id"]),
        sa.UniqueConstraint(
            "snapshot_id", "shape_code", "carat_anchor", "color_code", "clarity_code",
            name="uix_market_snapshot_quote",
        ),
        schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_data_quotes_quote_id",
        "market_data_quotes", ["quote_id"], schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_data_quotes_snapshot_id",
        "market_data_quotes", ["snapshot_id"], schema="diamond_market",
    )
    op.add_column(
        "stone_valuations",
        sa.Column("market_snapshot_id", sa.Integer(), nullable=True),
        schema="diamond_oltp",
    )
    op.add_column(
        "stone_valuations",
        sa.Column("applicability_note", sa.Text(), nullable=True),
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_oltp_stone_valuations_market_snapshot_id",
        "stone_valuations", ["market_snapshot_id"], schema="diamond_oltp",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diamond_oltp_stone_valuations_market_snapshot_id",
        table_name="stone_valuations", schema="diamond_oltp",
    )
    op.drop_column("stone_valuations", "applicability_note", schema="diamond_oltp")
    op.drop_column("stone_valuations", "market_snapshot_id", schema="diamond_oltp")
    op.drop_index(
        "ix_diamond_market_market_data_quotes_snapshot_id",
        table_name="market_data_quotes", schema="diamond_market",
    )
    op.drop_index(
        "ix_diamond_market_market_data_quotes_quote_id",
        table_name="market_data_quotes", schema="diamond_market",
    )
    op.drop_table("market_data_quotes", schema="diamond_market")
    op.drop_index(
        "ix_diamond_market_market_data_snapshots_status",
        table_name="market_data_snapshots", schema="diamond_market",
    )
    op.drop_index(
        "ix_diamond_market_market_data_snapshots_provider_code",
        table_name="market_data_snapshots", schema="diamond_market",
    )
    op.drop_index(
        "ix_diamond_market_market_data_snapshots_snapshot_id",
        table_name="market_data_snapshots", schema="diamond_market",
    )
    op.drop_table("market_data_snapshots", schema="diamond_market")
    op.drop_table("market_data_providers", schema="diamond_market")
