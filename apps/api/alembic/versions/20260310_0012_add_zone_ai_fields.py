"""add zone ai fields

Revision ID: 20260310_0012
Revises: 20260310_0011
Create Date: 2026-03-10 22:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260310_0012"
down_revision = "20260310_0011"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_names() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    columns = _column_names("zone_analysis_parcels")

    additions = [
        ("ai_recommendation", sa.Column("ai_recommendation", sa.String(length=20), nullable=True)),
        ("ai_confidence_score", sa.Column("ai_confidence_score", sa.Float(), nullable=True)),
        ("ai_reason_codes", sa.Column("ai_reason_codes", sa.Text(), nullable=True)),
        ("ai_reason_text", sa.Column("ai_reason_text", sa.String(length=300), nullable=True)),
        ("ai_model_version", sa.Column("ai_model_version", sa.String(length=40), nullable=True)),
        ("ai_applied", sa.Column("ai_applied", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("selection_origin", sa.Column("selection_origin", sa.String(length=20), nullable=False, server_default="rule")),
        ("anomaly_codes", sa.Column("anomaly_codes", sa.Text(), nullable=True)),
        ("anomaly_level", sa.Column("anomaly_level", sa.String(length=20), nullable=True)),
        ("building_confidence", sa.Column("building_confidence", sa.String(length=20), nullable=True)),
        ("household_confidence", sa.Column("household_confidence", sa.String(length=20), nullable=True)),
        ("floor_area_ratio_confidence", sa.Column("floor_area_ratio_confidence", sa.String(length=20), nullable=True)),
    ]
    for name, column in additions:
        if name not in columns:
            op.add_column("zone_analysis_parcels", column)

    if "zone_ai_feedbacks" not in _table_names():
        op.create_table(
            "zone_ai_feedbacks",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("zone_analysis_id", sa.String(length=36), nullable=False),
            sa.Column("pnu", sa.String(length=19), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("ai_model_version", sa.String(length=40), nullable=True),
            sa.Column("ai_recommendation", sa.String(length=20), nullable=True),
            sa.Column("final_decision", sa.String(length=20), nullable=False),
            sa.Column("decision_origin", sa.String(length=20), nullable=False, server_default="user"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["zone_analysis_id"], ["zone_analyses.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_zone_ai_feedbacks_zone_analysis_id"), "zone_ai_feedbacks", ["zone_analysis_id"], unique=False)
        op.create_index(op.f("ix_zone_ai_feedbacks_pnu"), "zone_ai_feedbacks", ["pnu"], unique=False)
        op.create_index(op.f("ix_zone_ai_feedbacks_user_id"), "zone_ai_feedbacks", ["user_id"], unique=False)
        op.create_index(op.f("ix_zone_ai_feedbacks_created_at"), "zone_ai_feedbacks", ["created_at"], unique=False)


def downgrade() -> None:
    if "zone_ai_feedbacks" in _table_names():
        op.drop_index(op.f("ix_zone_ai_feedbacks_created_at"), table_name="zone_ai_feedbacks")
        op.drop_index(op.f("ix_zone_ai_feedbacks_user_id"), table_name="zone_ai_feedbacks")
        op.drop_index(op.f("ix_zone_ai_feedbacks_pnu"), table_name="zone_ai_feedbacks")
        op.drop_index(op.f("ix_zone_ai_feedbacks_zone_analysis_id"), table_name="zone_ai_feedbacks")
        op.drop_table("zone_ai_feedbacks")

    columns = _column_names("zone_analysis_parcels")
    for name in [
        "floor_area_ratio_confidence",
        "household_confidence",
        "building_confidence",
        "anomaly_level",
        "anomaly_codes",
        "selection_origin",
        "ai_applied",
        "ai_model_version",
        "ai_reason_text",
        "ai_reason_codes",
        "ai_confidence_score",
        "ai_recommendation",
    ]:
        if name in columns:
            op.drop_column("zone_analysis_parcels", name)
