"""add parcels table for map lookup

Revision ID: 20260304_0003
Revises: 20260302_0002
Create Date: 2026-03-04 14:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260304_0003"
down_revision: Union[str, None] = "20260302_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    if "parcels" not in tables:
        op.create_table(
            "parcels",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("pnu", sa.String(length=19), nullable=False),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("lng", sa.Float(), nullable=False),
            sa.Column("area", sa.Float(), nullable=True),
            sa.Column("price_current", sa.BigInteger(), nullable=True),
            sa.Column("price_previous", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("pnu"),
        )

    refreshed = sa.inspect(bind)
    indexes = {idx["name"] for idx in refreshed.get_indexes("parcels")} if "parcels" in refreshed.get_table_names() else set()
    if "ix_parcels_pnu" not in indexes:
        op.create_index("ix_parcels_pnu", "parcels", ["pnu"], unique=True)

    if dialect == "postgresql":
        columns = {col["name"] for col in refreshed.get_columns("parcels")}
        if "geog" not in columns:
            op.execute("ALTER TABLE parcels ADD COLUMN geog GEOGRAPHY(POINT, 4326)")
        if "geom" not in columns:
            op.execute("ALTER TABLE parcels ADD COLUMN geom GEOMETRY(POLYGON, 4326)")

        refreshed_indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes("parcels")}
        if "idx_parcels_geog_gist" not in refreshed_indexes:
            op.execute("CREATE INDEX idx_parcels_geog_gist ON parcels USING GIST (geog)")
        if "idx_parcels_geom_gist" not in refreshed_indexes:
            op.execute("CREATE INDEX idx_parcels_geom_gist ON parcels USING GIST (geom)")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "parcels" not in tables:
        return

    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_parcels_geog_gist")
        op.execute("DROP INDEX IF EXISTS idx_parcels_geom_gist")
        op.execute("ALTER TABLE parcels DROP COLUMN IF EXISTS geog")
        op.execute("ALTER TABLE parcels DROP COLUMN IF EXISTS geom")

    indexes = {idx["name"] for idx in inspector.get_indexes("parcels")}
    if "ix_parcels_pnu" in indexes:
        op.drop_index("ix_parcels_pnu", table_name="parcels")
    op.drop_table("parcels")
