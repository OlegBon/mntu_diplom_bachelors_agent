"""Allow fictional provider analytics for existing synthetic manifests.

Revision ID: 0020_demo_provider_analytics_eligibility
Revises: 0019_demo_som_artifacts
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0020_demo_provider_analytics_eligibility"
down_revision: Union[str, Sequence[str], None] = "0019_demo_som_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PREVIOUS = '["demo_operations", "synthetic_som"]'
_CURRENT = '["demo_operations", "synthetic_som", "demo_provider_analytics"]'


def upgrade() -> None:
    """Extend only known synthetic manifests; reports and valuations stay untouched."""
    op.execute(
        "UPDATE diamond_oltp.demo_datasets "
        f"SET analysis_eligibility = '{_CURRENT}' "
        "WHERE provenance LIKE 'synthetic-demo-v%' "
        f"AND analysis_eligibility = '{_PREVIOUS}'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE diamond_oltp.demo_datasets "
        f"SET analysis_eligibility = '{_PREVIOUS}' "
        "WHERE provenance LIKE 'synthetic-demo-v%' "
        f"AND analysis_eligibility = '{_CURRENT}'"
    )
