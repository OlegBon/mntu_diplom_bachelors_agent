"""Persist immutable synthetic SOM artifacts and report assignments.

Revision ID: 0019_demo_som_artifacts
Revises: 0018_admin_demo_access_opt_in
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0019_demo_som_artifacts"
down_revision: Union[str, Sequence[str], None] = "0018_admin_demo_access_opt_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demo_som_artifacts",
        sa.Column("artifact_id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_version", sa.String(length=64), nullable=False),
        sa.Column("policy_scenario_id", sa.String(length=64), nullable=False),
        sa.Column("dataset_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("training_seed", sa.Integer(), nullable=False),
        sa.Column("grid_size", sa.Integer(), nullable=False),
        sa.Column("feature_schema", sa.Text(), nullable=False),
        sa.Column("normalization", sa.Text(), nullable=False),
        sa.Column("coverage", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["dataset_id"], ["diamond_oltp.demo_datasets.dataset_id"]),
        sa.UniqueConstraint("dataset_id", "artifact_version", "content_sha256", name="uq_demo_som_artifact_content"),
        schema="diamond_oltp",
    )
    op.create_index("ix_demo_som_artifacts_dataset_created", "demo_som_artifacts", ["dataset_id", "created_at"], schema="diamond_oltp")
    op.create_table(
        "demo_som_assignments",
        sa.Column("assignment_id", sa.Integer(), primary_key=True),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.String(length=20), nullable=False),
        sa.Column("som_x", sa.Integer(), nullable=False),
        sa.Column("som_y", sa.Integer(), nullable=False),
        sa.Column("distance", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("selected_provider", sa.String(length=100), nullable=False),
        sa.Column("selected_reference_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["diamond_oltp.demo_som_artifacts.artifact_id"]),
        sa.ForeignKeyConstraint(["report_id"], ["diamond_oltp.diamond_reports.report_id"]),
        sa.UniqueConstraint("artifact_id", "report_id", name="uq_demo_som_assignment_report"),
        schema="diamond_oltp",
    )
    op.create_index("ix_demo_som_assignments_artifact_cell", "demo_som_assignments", ["artifact_id", "som_x", "som_y"], schema="diamond_oltp")


def downgrade() -> None:
    op.drop_index("ix_demo_som_assignments_artifact_cell", table_name="demo_som_assignments", schema="diamond_oltp")
    op.drop_table("demo_som_assignments", schema="diamond_oltp")
    op.drop_index("ix_demo_som_artifacts_dataset_created", table_name="demo_som_artifacts", schema="diamond_oltp")
    op.drop_table("demo_som_artifacts", schema="diamond_oltp")
