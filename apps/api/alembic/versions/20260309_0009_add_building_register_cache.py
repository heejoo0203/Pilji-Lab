"""add building register cache

Revision ID: 20260309_0009
Revises: 20260307_0008
Create Date: 2026-03-09 23:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260309_0009"
down_revision = "20260307_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "building_register_caches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pnu", sa.String(length=19), nullable=False),
        sa.Column("has_building_register", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("building_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("aged_building_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("residential_building_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("approval_year_sum", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("approval_year_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("average_approval_year", sa.Integer(), nullable=True),
        sa.Column("total_floor_area_sqm", sa.Float(), nullable=True),
        sa.Column("site_area_sqm", sa.Float(), nullable=True),
        sa.Column("floor_area_ratio", sa.Float(), nullable=True),
        sa.Column("primary_purpose_name", sa.String(length=120), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pnu"),
    )
    op.create_index("ix_building_register_caches_pnu", "building_register_caches", ["pnu"], unique=True)
    op.create_index("ix_building_register_caches_synced_at", "building_register_caches", ["synced_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_building_register_caches_synced_at", table_name="building_register_caches")
    op.drop_index("ix_building_register_caches_pnu", table_name="building_register_caches")
    op.drop_table("building_register_caches")
