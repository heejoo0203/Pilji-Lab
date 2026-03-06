"""alter parcels.geom to multipolygon

Revision ID: 20260306_0007
Revises: 20260306_0006
Create Date: 2026-03-06 23:55:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260306_0007"
down_revision: Union[str, None] = "20260306_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "parcels" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("parcels")}
    if "geom" not in columns:
        return

    op.execute(
        """
        ALTER TABLE parcels
        ALTER COLUMN geom TYPE GEOMETRY(MULTIPOLYGON, 4326)
        USING (
          CASE
            WHEN geom IS NULL THEN NULL
            ELSE ST_Multi(ST_CollectionExtract(geom, 3))
          END
        )
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "parcels" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("parcels")}
    if "geom" not in columns:
        return

    op.execute(
        """
        ALTER TABLE parcels
        ALTER COLUMN geom TYPE GEOMETRY(POLYGON, 4326)
        USING (
          CASE
            WHEN geom IS NULL THEN NULL
            ELSE ST_GeometryN(geom, 1)
          END
        )
        """
    )
