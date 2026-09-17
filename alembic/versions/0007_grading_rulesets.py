"""Register immutable grading rulesets without recalculating reports.

Revision ID: 0007_grading_rulesets
Revises: 0006_expert_activation
Create Date: 2026-09-17

Existing reports keep their stored grades. Rows without a historical rule code
are labelled ``legacy-unversioned-v1`` instead of being inferred as IDC.
"""

from typing import Sequence, Union
from datetime import date

from alembic import op
import sqlalchemy as sa


revision: str = "0007_grading_rulesets"
down_revision: Union[str, Sequence[str], None] = "0006_expert_activation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grading_rulesets",
        sa.Column("ruleset_id", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("source_edition", sa.String(length=100), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=32), nullable=False),
        sa.Column("scope_note", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("ruleset_id"),
        schema="diamond_oltp",
    )
    grading_rulesets = sa.table(
        "grading_rulesets",
        sa.column("ruleset_id", sa.String),
        sa.column("display_name", sa.String),
        sa.column("source_title", sa.String),
        sa.column("source_edition", sa.String),
        sa.column("effective_from", sa.Date),
        sa.column("algorithm_version", sa.String),
        sa.column("scope_note", sa.Text),
        sa.column("is_active", sa.Boolean),
        schema="diamond_oltp",
    )
    op.bulk_insert(
        grading_rulesets,
        [
            {
                "ruleset_id": "legacy-unversioned-v1",
                "display_name": "Історичні записи без ruleset",
                "source_title": "Legacy Diamant ID import",
                "source_edition": None,
                "effective_from": None,
                "algorithm_version": "none",
                "scope_note": "Імпортовані записи; правила не реконструюються і не перераховуються.",
                "is_active": False,
            },
            {
                "ruleset_id": "idc-demo-v1",
                "display_name": "IDC demo v1",
                "source_title": "IDC Rules for Grading Polished Diamonds",
                "source_edition": "6th edition, July 2013",
                "effective_from": date(2026, 9, 15),
                "algorithm_version": "diamond-calculator-v1",
                "scope_note": "Спрощений server-side preview: table, depth, crown і pavilion; не є повною реалізацією IDC 2013.",
                "is_active": True,
            },
        ],
    )
    op.execute(
        "UPDATE diamond_oltp.diamond_reports "
        "SET calculation_rule_version = 'legacy-unversioned-v1' "
        "WHERE calculation_rule_version IS NULL OR calculation_rule_version = ''"
    )
    op.create_index(
        "ix_diamond_oltp_diamond_reports_calculation_rule_version",
        "diamond_reports",
        ["calculation_rule_version"],
        unique=False,
        schema="diamond_oltp",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diamond_oltp_diamond_reports_calculation_rule_version",
        table_name="diamond_reports",
        schema="diamond_oltp",
    )
    op.execute(
        "UPDATE diamond_oltp.diamond_reports "
        "SET calculation_rule_version = NULL "
        "WHERE calculation_rule_version = 'legacy-unversioned-v1'"
    )
    op.drop_table("grading_rulesets", schema="diamond_oltp")
