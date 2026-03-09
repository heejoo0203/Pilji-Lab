"""add zone accuracy fields

Revision ID: 20260310_0011
Revises: 20260310_0010
Create Date: 2026-03-10 18:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260310_0011"
down_revision = "20260310_0010"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _column_names("zone_analysis_parcels")

    if "overlap_area_sqm" not in columns:
        op.add_column("zone_analysis_parcels", sa.Column("overlap_area_sqm", sa.Float(), nullable=False, server_default="0"))
    if "centroid_in" not in columns:
        op.add_column("zone_analysis_parcels", sa.Column("centroid_in", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    if "selected_by_rule" not in columns:
        op.add_column("zone_analysis_parcels", sa.Column("selected_by_rule", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    if "inclusion_mode" not in columns:
        op.add_column("zone_analysis_parcels", sa.Column("inclusion_mode", sa.String(length=30), nullable=False, server_default="excluded"))
    if "confidence_score" not in columns:
        op.add_column("zone_analysis_parcels", sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    columns = _column_names("zone_analysis_parcels")

    if "confidence_score" in columns:
        op.drop_column("zone_analysis_parcels", "confidence_score")
    if "inclusion_mode" in columns:
        op.drop_column("zone_analysis_parcels", "inclusion_mode")
    if "selected_by_rule" in columns:
        op.drop_column("zone_analysis_parcels", "selected_by_rule")
    if "centroid_in" in columns:
        op.drop_column("zone_analysis_parcels", "centroid_in")
    if "overlap_area_sqm" in columns:
        op.drop_column("zone_analysis_parcels", "overlap_area_sqm")
