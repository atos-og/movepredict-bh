"""Estatísticas históricas de velocidade por linha e hora."""

import sqlalchemy as sa
from alembic import op

revision = "20260714_04"
down_revision = "20260714_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "route_hour_speed_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id"), nullable=False),
        sa.Column("local_hour", sa.Integer(), nullable=False),
        sa.Column("average_speed_kmh", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("route_id", "local_hour", name="uq_route_hour_speed_stat"),
        sa.CheckConstraint("local_hour BETWEEN 0 AND 23", name="ck_route_hour_speed_local_hour"),
        sa.CheckConstraint("average_speed_kmh > 0", name="ck_route_hour_speed_average"),
        sa.CheckConstraint("sample_size >= 0", name="ck_route_hour_speed_sample_size"),
    )
    op.create_index("ix_route_hour_speed_stats_route_id", "route_hour_speed_stats", ["route_id"])


def downgrade() -> None:
    op.drop_table("route_hour_speed_stats")
