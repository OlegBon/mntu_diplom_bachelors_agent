"""Add reversible expert account deactivation.

Revision ID: 0006_expert_activation
Revises: 0005_public_passports
Create Date: 2026-09-16

Existing expert accounts remain active. This preserves every foreign-key
relationship while allowing an administrator to revoke future access.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_expert_activation"
down_revision: Union[str, Sequence[str], None] = "0005_public_passports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "experts",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        schema="diamond_oltp",
    )
    op.alter_column("experts", "is_active", server_default=None, schema="diamond_oltp")


def downgrade() -> None:
    op.drop_column("experts", "is_active", schema="diamond_oltp")
