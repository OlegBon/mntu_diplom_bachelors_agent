"""Add per-administrator synthetic demo access opt-in.

Revision ID: 0018_admin_demo_access_opt_in
Revises: 0017_demo_workflow_index_convergence
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0018_admin_demo_access_opt_in"
down_revision: Union[str, Sequence[str], None] = "0017_demo_workflow_index_convergence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "experts",
        sa.Column("demo_access_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        schema="diamond_oltp",
    )


def downgrade() -> None:
    op.drop_column("experts", "demo_access_enabled", schema="diamond_oltp")
