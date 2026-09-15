"""Add the factual examination date and missing wizard reference values.

Revision ID: 0004_report_wizard
Revises: 0003_media_assets
Create Date: 2026-09-15

The examination date is nullable so legacy reports remain historically honest:
their creation date is not evidence of the date of examination.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_report_wizard"
down_revision: Union[str, Sequence[str], None] = "0003_media_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diamond_reports",
        sa.Column("examination_date", sa.Date(), nullable=True),
        schema="diamond_oltp",
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
            {"category": "girdle_thickness", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("thin", "Thin"), ("medium", "Medium"), ("slightly_thick", "Slightly Thick"), ("thick", "Thick")))
        ]
        + [
            {"category": "culet_size", "code": code, "label": label, "sort_order": order, "is_active": True}
            for order, (code, label) in enumerate((("none", "None"), ("very_small", "Very Small"), ("small", "Small"), ("medium", "Medium")))
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM diamond_market.reference_values WHERE category IN ('girdle_thickness', 'culet_size')")
    op.drop_column("diamond_reports", "examination_date", schema="diamond_oltp")
