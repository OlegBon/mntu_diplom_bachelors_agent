"""Create the initial Diamant ID tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-14

This revision creates tables only. The three MariaDB databases must already
exist; use scripts/bootstrap_mariadb_databases.py before `alembic upgrade` on a
new local environment. Do not run downgrade against valued local data.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experts",
        sa.Column("expert_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("first_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=True),
        sa.Column("middle_name", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("admin", "gemologist"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_oltp_experts_expert_id",
        "experts",
        ["expert_id"],
        schema="diamond_oltp",
    )
    op.create_table(
        "diamond_reports",
        sa.Column("report_id", sa.String(length=20), primary_key=True),
        sa.Column("report_date", sa.DateTime(), nullable=False),
        sa.Column("shape", sa.String(length=50), nullable=False),
        sa.Column("measurements_length", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("measurements_width", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("measurements_depth", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("table_percent", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("depth_percent", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("crown_angle", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("pavilion_angle", sa.DECIMAL(precision=5, scale=2)),
        sa.Column("girdle_thickness", sa.String(length=50)),
        sa.Column("culet_size", sa.String(length=50)),
        sa.Column("carat_weight", sa.DECIMAL(precision=10, scale=2)),
        sa.Column("color_grade", sa.Integer()),
        sa.Column("clarity_grade", sa.Integer()),
        sa.Column("cut_grade", sa.Integer()),
        sa.Column("polish_grade", sa.Integer()),
        sa.Column("symmetry_grade", sa.Integer()),
        sa.Column("proportions_grade", sa.Integer()),
        sa.Column("fluorescence_grade", sa.Integer()),
        sa.Column("stone_origin", sa.Integer()),
        sa.Column("expert_id", sa.Integer(), nullable=True),
        sa.Column("evaluation_time_sec", sa.Integer()),
        sa.Column("expert_comment", sa.Text(), nullable=True),
        sa.Column("report_notes_length", sa.Integer()),
        sa.Column("report_sentiment", sa.Integer()),
        sa.Column("plotting_image", sa.String(length=255), nullable=True),
        sa.Column("real_image", sa.String(length=255), nullable=True),
        sa.Column("price", sa.DECIMAL(precision=12, scale=2)),
        sa.Column("is_investment_grade", sa.Boolean(), nullable=True),
        sa.Column("is_report_rejected", sa.Boolean(), nullable=True),
        sa.Column("is_sold", sa.Boolean(), nullable=True),
        sa.Column("days_on_market", sa.Integer(), nullable=True),
        sa.Column("sale_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["expert_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index(
        "ix_diamond_oltp_diamond_reports_report_id",
        "diamond_reports",
        ["report_id"],
        schema="diamond_oltp",
    )
    op.create_table(
        "grade_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("grade_value", sa.Integer(), nullable=False),
        sa.Column("grade_label", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("category", "grade_value", name="uix_category_grade"),
        schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_grade_mappings_id",
        "grade_mappings",
        ["id"],
        schema="diamond_market",
    )
    op.create_table(
        "market_price_reference",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("price_index_value", sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        schema="diamond_market",
    )
    op.create_index(
        "ix_diamond_market_market_price_reference_id",
        "market_price_reference",
        ["id"],
        schema="diamond_market",
    )
    op.create_table(
        "ml_results",
        sa.Column("report_id", sa.String(length=20), primary_key=True),
        sa.Column("predicted_price", sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column("predicted_class", sa.String(length=50), nullable=True),
        sa.Column("cluster_label", sa.String(length=50), nullable=True),
        sa.Column("som_x", sa.Integer(), nullable=True),
        sa.Column("som_y", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        schema="diamond_analytics",
    )


def downgrade() -> None:
    op.drop_table("ml_results", schema="diamond_analytics")
    op.drop_index(
        "ix_diamond_market_market_price_reference_id",
        table_name="market_price_reference",
        schema="diamond_market",
    )
    op.drop_table("market_price_reference", schema="diamond_market")
    op.drop_index(
        "ix_diamond_market_grade_mappings_id",
        table_name="grade_mappings",
        schema="diamond_market",
    )
    op.drop_table("grade_mappings", schema="diamond_market")
    op.drop_index(
        "ix_diamond_oltp_diamond_reports_report_id",
        table_name="diamond_reports",
        schema="diamond_oltp",
    )
    op.drop_table("diamond_reports", schema="diamond_oltp")
    op.drop_index(
        "ix_diamond_oltp_experts_expert_id",
        table_name="experts",
        schema="diamond_oltp",
    )
    op.drop_table("experts", schema="diamond_oltp")
