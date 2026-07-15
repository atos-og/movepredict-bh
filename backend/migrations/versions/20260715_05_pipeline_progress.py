"""Progresso da deteccao, retencao segura e previsoes atuais sem duplicatas."""

import sqlalchemy as sa
from alembic import op

revision = "20260715_05"
down_revision = "20260714_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vehicle_positions",
        sa.Column("arrival_detection_checked_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_vehicle_positions_arrival_detection_checked",
        "vehicle_positions",
        ["arrival_detection_checked_at", "observed_at"],
    )
    op.drop_constraint("arrival_events_position_id_fkey", "arrival_events", type_="foreignkey")
    op.create_foreign_key(
        "arrival_events_position_id_fkey",
        "arrival_events",
        "vehicle_positions",
        ["position_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _replace_current_arrivals_view(deduplicate=True)


def downgrade() -> None:
    _replace_current_arrivals_view(deduplicate=False)
    op.drop_constraint("arrival_events_position_id_fkey", "arrival_events", type_="foreignkey")
    op.create_foreign_key(
        "arrival_events_position_id_fkey",
        "arrival_events",
        "vehicle_positions",
        ["position_id"],
        ["id"],
    )
    op.drop_index("ix_vehicle_positions_arrival_detection_checked", table_name="vehicle_positions")
    op.drop_column("vehicle_positions", "arrival_detection_checked_at")


def _replace_current_arrivals_view(*, deduplicate: bool) -> None:
    distinct = (
        "DISTINCT ON (ap.stop_id, ap.route_id, ap.trip_id, ap.vehicle_id, ap.model_version)"
        if deduplicate
        else ""
    )
    ordering = (
        "ORDER BY ap.stop_id, ap.route_id, ap.trip_id, ap.vehicle_id, "
        "ap.model_version, ap.generated_at DESC"
        if deduplicate
        else ""
    )
    op.execute(
        f"""
        CREATE OR REPLACE VIEW current_arrival_predictions AS
        SELECT {distinct}
            s.gtfs_stop_id AS stop_id,
            r.gtfs_route_id AS route_id,
            t.gtfs_trip_id AS trip_id,
            v.source_vehicle_id AS vehicle_id,
            ap.generated_at,
            ap.predicted_arrival,
            ap.uncertainty_seconds,
            ap.model_version,
            ap.prediction_basis,
            ap.sample_size,
            ap.horizon_seconds
        FROM arrival_predictions ap
        JOIN transit_stops s ON s.id = ap.stop_id
        JOIN transit_routes r ON r.id = ap.route_id
        LEFT JOIN transit_trips t ON t.id = ap.trip_id
        LEFT JOIN vehicles v ON v.id = ap.vehicle_id
        WHERE ap.predicted_arrival >= now() - interval '2 minutes'
        {ordering}
        """
    )
