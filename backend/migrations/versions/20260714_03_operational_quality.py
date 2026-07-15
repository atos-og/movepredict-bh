"""Métricas operacionais, contexto de ETA e consultas SQL estáveis."""

import sqlalchemy as sa
from alembic import op

revision = "20260714_03"
down_revision = "20260711_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("arrival_predictions", sa.Column("prediction_basis", sa.String(50)))
    op.add_column("arrival_predictions", sa.Column("sample_size", sa.Integer()))
    op.add_column("arrival_predictions", sa.Column("horizon_seconds", sa.Integer()))
    op.create_check_constraint(
        "ck_arrival_prediction_sample_size",
        "arrival_predictions",
        "sample_size IS NULL OR sample_size >= 0",
    )
    op.create_check_constraint(
        "ck_arrival_prediction_horizon",
        "arrival_predictions",
        "horizon_seconds IS NULL OR horizon_seconds >= 0",
    )
    op.create_index(
        "ix_arrival_predictions_stop_predicted",
        "arrival_predictions",
        ["stop_id", "predicted_arrival"],
    )
    op.create_index(
        "ix_vehicle_positions_match_observed",
        "vehicle_positions",
        ["trip_match_method", "observed_at"],
    )
    op.create_index(
        "ix_collection_runs_started_status", "collection_runs", ["started_at", "status"]
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("collection_run_id", sa.Integer(), sa.ForeignKey("collection_runs.id")),
        sa.Column("positions_inspected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positions_matched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "positions_rejected_no_candidate", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("positions_rejected_ambiguous", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("arrivals_detected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("predictions_labeled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("predictions_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("error_type", sa.String(100)),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_pipeline_runs_started_at", "pipeline_runs", ["started_at"])
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])
    op.execute(
        """
        CREATE VIEW current_vehicle_positions AS
        SELECT DISTINCT ON (vp.vehicle_id)
            v.source_vehicle_id AS vehicle_id,
            r.gtfs_route_id AS route_id,
            t.gtfs_trip_id AS trip_id,
            vp.observed_at,
            vp.ingested_at,
            vp.latitude,
            vp.longitude,
            vp.speed_kmh,
            vp.bearing,
            vp.trip_match_confidence,
            vp.trip_match_method
        FROM vehicle_positions vp
        JOIN vehicles v ON v.id = vp.vehicle_id AND v.is_active
        LEFT JOIN transit_routes r ON r.id = vp.route_id
        LEFT JOIN transit_trips t ON t.id = vp.trip_id
        ORDER BY vp.vehicle_id, vp.observed_at DESC
        """
    )
    op.execute(
        """
        CREATE VIEW current_arrival_predictions AS
        SELECT
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
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW current_arrival_predictions")
    op.execute("DROP VIEW current_vehicle_positions")
    op.drop_table("pipeline_runs")
    op.drop_index("ix_collection_runs_started_status", table_name="collection_runs")
    op.drop_index("ix_vehicle_positions_match_observed", table_name="vehicle_positions")
    op.drop_index("ix_arrival_predictions_stop_predicted", table_name="arrival_predictions")
    op.drop_constraint("ck_arrival_prediction_horizon", "arrival_predictions")
    op.drop_constraint("ck_arrival_prediction_sample_size", "arrival_predictions")
    op.drop_column("arrival_predictions", "horizon_seconds")
    op.drop_column("arrival_predictions", "sample_size")
    op.drop_column("arrival_predictions", "prediction_basis")
