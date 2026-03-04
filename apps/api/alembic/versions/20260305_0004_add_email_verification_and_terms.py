"""add email verification table and user terms columns

Revision ID: 20260305_0004
Revises: 20260304_0003
Create Date: 2026-03-05 10:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260305_0004"
down_revision: Union[str, None] = "20260304_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "email_verifications" not in tables:
        op.create_table(
            "email_verifications",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("purpose", sa.String(length=30), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=100), nullable=True),
            sa.Column("code_hash", sa.String(length=128), nullable=False),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    refreshed = sa.inspect(bind)
    if "email_verifications" in refreshed.get_table_names():
        indexes = {idx["name"] for idx in refreshed.get_indexes("email_verifications")}
        if "ix_email_verifications_purpose" not in indexes:
            op.create_index(
                "ix_email_verifications_purpose",
                "email_verifications",
                ["purpose"],
                unique=False,
            )
        if "ix_email_verifications_email" not in indexes:
            op.create_index(
                "ix_email_verifications_email",
                "email_verifications",
                ["email"],
                unique=False,
            )
        if "ix_email_verifications_expires_at" not in indexes:
            op.create_index(
                "ix_email_verifications_expires_at",
                "email_verifications",
                ["expires_at"],
                unique=False,
            )

    user_columns = {col["name"] for col in sa.inspect(bind).get_columns("users")}
    if "terms_version" not in user_columns:
        op.add_column(
            "users",
            sa.Column("terms_version", sa.String(length=30), nullable=False, server_default="2026-03-05-v1"),
        )
    if "terms_snapshot" not in user_columns:
        op.add_column(
            "users",
            sa.Column("terms_snapshot", sa.Text(), nullable=False, server_default=""),
        )
    if "terms_accepted_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "terms_accepted_at" in user_columns:
            op.drop_column("users", "terms_accepted_at")
        if "terms_snapshot" in user_columns:
            op.drop_column("users", "terms_snapshot")
        if "terms_version" in user_columns:
            op.drop_column("users", "terms_version")

    if "email_verifications" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("email_verifications")}
        if "ix_email_verifications_expires_at" in indexes:
            op.drop_index("ix_email_verifications_expires_at", table_name="email_verifications")
        if "ix_email_verifications_email" in indexes:
            op.drop_index("ix_email_verifications_email", table_name="email_verifications")
        if "ix_email_verifications_purpose" in indexes:
            op.drop_index("ix_email_verifications_purpose", table_name="email_verifications")
        op.drop_table("email_verifications")
