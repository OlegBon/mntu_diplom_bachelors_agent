"""Normalize report core data without discarding legacy compatibility columns.

Revision ID: 0002_report_core
Revises: 0001_initial_schema
Create Date: 2026-09-14

The data copy targets local MariaDB only. Do not run this revision against a
valued database without a backup and explicit approval. The PostgreSQL move is
a later, separate migration project.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_report_core"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stones",
        sa.Column("stone_id", sa.Integer(), primary_key=True),
        sa.Column("legacy_source_report_id", sa.String(length=20), nullable=True, unique=True),
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
        sa.Column("polish_grade", sa.Integer()),
        sa.Column("symmetry_grade", sa.Integer()),
        sa.Column("fluorescence_grade", sa.Integer()),
        sa.Column("origin", sa.String(length=24), nullable=False, server_default="unknown"),
        sa.Column("legacy_origin_code", sa.Integer()),
        sa.Column("treatment_status", sa.String(length=24), nullable=False, server_default="not_assessed"),
        sa.Column("identification_status", sa.String(length=24), nullable=False, server_default="preliminary"),
        sa.Column("identification_method", sa.String(length=255)),
        sa.Column("identification_conclusion", sa.Text()),
        sa.Column("market_status", sa.String(length=24), nullable=False, server_default="not_for_sale"),
        sa.Column("legacy_sale_date", sa.DateTime()),
        sa.Column("legacy_days_on_market", sa.Integer()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_stones_stone_id", "stones", ["stone_id"], schema="diamond_oltp")

    op.add_column("diamond_reports", sa.Column("stone_id", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("created_at", sa.DateTime(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("updated_at", sa.DateTime(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("issued_at", sa.DateTime(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("issued_by_id", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("system_proportions_grade", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("system_cut_grade", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("calculation_rule_version", sa.String(length=32), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("expert_proportions_grade", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("expert_cut_grade", sa.Integer(), nullable=True), schema="diamond_oltp")
    op.add_column("diamond_reports", sa.Column("expert_confirmed_at", sa.DateTime(), nullable=True), schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_diamond_reports_stone_id", "diamond_reports", ["stone_id"], schema="diamond_oltp")
    op.create_foreign_key(
        "fk_diamond_reports_stone_id",
        "diamond_reports",
        "stones",
        ["stone_id"],
        ["stone_id"],
        source_schema="diamond_oltp",
        referent_schema="diamond_oltp",
    )
    op.create_foreign_key(
        "fk_diamond_reports_issued_by_id",
        "diamond_reports",
        "experts",
        ["issued_by_id"],
        ["expert_id"],
        source_schema="diamond_oltp",
        referent_schema="diamond_oltp",
    )

    op.create_table(
        "report_events",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=16)),
        sa.Column("to_status", sa.String(length=16)),
        sa.Column("actor_id", sa.Integer()),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_report_events_event_id", "report_events", ["event_id"], schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_report_events_report_id", "report_events", ["report_id"], schema="diamond_oltp")

    op.create_table(
        "stone_valuations",
        sa.Column("valuation_id", sa.Integer(), primary_key=True),
        sa.Column("stone_id", sa.Integer(), nullable=False),
        sa.Column("valuation_kind", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.DECIMAL(precision=14, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("unit", sa.String(length=24), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_reference", sa.String(length=255)),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["stone_id"], ["diamond_oltp.stones.stone_id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["diamond_oltp.experts.expert_id"]),
        schema="diamond_oltp",
    )
    op.create_index("ix_diamond_oltp_stone_valuations_valuation_id", "stone_valuations", ["valuation_id"], schema="diamond_oltp")
    op.create_index("ix_diamond_oltp_stone_valuations_stone_id", "stone_valuations", ["stone_id"], schema="diamond_oltp")

    op.create_table(
        "reference_values",
        sa.Column("reference_id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("category", "code", name="uix_reference_category_code"),
        schema="diamond_market",
    )
    op.create_index("ix_diamond_market_reference_values_reference_id", "reference_values", ["reference_id"], schema="diamond_market")

    # MariaDB-only data backfill. Codes 2 and 3 deliberately remain unknown:
    # old seed data never documented their meaning.
    op.execute(
        """
        INSERT INTO diamond_oltp.stones (
            legacy_source_report_id, shape, measurements_length, measurements_width,
            measurements_depth, table_percent, depth_percent, crown_angle,
            pavilion_angle, girdle_thickness, culet_size, carat_weight, color_grade,
            clarity_grade, polish_grade, symmetry_grade, fluorescence_grade, origin,
            legacy_origin_code, treatment_status, identification_status, market_status,
            legacy_sale_date, legacy_days_on_market, created_at, updated_at
        )
        SELECT report_id, shape, measurements_length, measurements_width,
            measurements_depth, table_percent, depth_percent, crown_angle,
            pavilion_angle, girdle_thickness, culet_size, carat_weight, color_grade,
            clarity_grade, polish_grade, symmetry_grade, fluorescence_grade,
            CASE stone_origin WHEN 0 THEN 'natural' WHEN 1 THEN 'lab_grown' ELSE 'unknown' END,
            stone_origin, 'not_assessed', 'preliminary',
            CASE WHEN is_sold THEN 'sold' ELSE 'not_for_sale' END,
            sale_date, days_on_market, report_date, report_date
        FROM diamond_oltp.diamond_reports
        """
    )
    op.execute(
        """
        UPDATE diamond_oltp.diamond_reports report_row
        INNER JOIN diamond_oltp.stones stone_row
            ON stone_row.legacy_source_report_id = report_row.report_id
        SET report_row.stone_id = stone_row.stone_id,
            report_row.status = 'draft',
            report_row.created_at = report_row.report_date,
            report_row.updated_at = report_row.report_date,
            report_row.system_proportions_grade = report_row.proportions_grade,
            report_row.system_cut_grade = report_row.cut_grade,
            report_row.calculation_rule_version = 'legacy-unverified'
        """
    )
    op.execute(
        """
        INSERT INTO diamond_oltp.report_events (report_id, action, to_status, actor_id, reason, created_at)
        SELECT report_id, 'legacy_import', 'draft', expert_id,
            'Imported from legacy DiamondReport; no issuance or expert confirmation inferred.', report_date
        FROM diamond_oltp.diamond_reports
        """
    )
    reference_values = sa.table(
        "reference_values",
        sa.column("category", sa.String),
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        schema="diamond_market",
    )
    op.bulk_insert(
        reference_values,
        [
            {"category": "shape", "code": code.lower(), "label": code, "sort_order": order, "is_active": True}
            for order, code in enumerate(("Round", "Princess", "Oval", "Emerald", "Cushion", "Pear", "Marquise", "Asscher", "Radiant", "Heart"))
        ]
        + [
            {"category": "report_status", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("draft", "Чернетка"), ("review", "На перевірці"), ("issued", "Видано"), ("void", "Відкликано")))
        ]
        + [
            {"category": "origin", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("unknown", "Невідомо"), ("natural", "Природний"), ("lab_grown", "Лабораторно вирощений"), ("other", "Інше")))
        ]
        + [
            {"category": "treatment_status", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("not_assessed", "Не оцінено"), ("none_detected", "Не виявлено"), ("disclosed", "Заявлено"), ("confirmed", "Підтверджено")))
        ]
        + [
            {"category": "identification_status", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("preliminary", "Попередньо"), ("confirmed", "Підтверджено"), ("inconclusive", "Невизначено")))
        ]
        + [
            {"category": "market_status", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("not_for_sale", "Не продається"), ("available", "Доступний"), ("reserved", "Зарезервовано"), ("sold", "Продано"), ("withdrawn", "Знято з пропозиції")))
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_diamond_market_reference_values_reference_id", table_name="reference_values", schema="diamond_market")
    op.drop_table("reference_values", schema="diamond_market")
    op.drop_index("ix_diamond_oltp_stone_valuations_stone_id", table_name="stone_valuations", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_stone_valuations_valuation_id", table_name="stone_valuations", schema="diamond_oltp")
    op.drop_table("stone_valuations", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_events_report_id", table_name="report_events", schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_report_events_event_id", table_name="report_events", schema="diamond_oltp")
    op.drop_table("report_events", schema="diamond_oltp")
    op.drop_constraint("fk_diamond_reports_issued_by_id", "diamond_reports", schema="diamond_oltp", type_="foreignkey")
    op.drop_constraint("fk_diamond_reports_stone_id", "diamond_reports", schema="diamond_oltp", type_="foreignkey")
    op.drop_index("ix_diamond_oltp_diamond_reports_stone_id", table_name="diamond_reports", schema="diamond_oltp")
    for column in (
        "expert_confirmed_at", "expert_cut_grade", "expert_proportions_grade",
        "calculation_rule_version", "system_cut_grade", "system_proportions_grade",
        "issued_by_id", "issued_at", "updated_at", "created_at", "status", "stone_id",
    ):
        op.drop_column("diamond_reports", column, schema="diamond_oltp")
    op.drop_index("ix_diamond_oltp_stones_stone_id", table_name="stones", schema="diamond_oltp")
    op.drop_table("stones", schema="diamond_oltp")
