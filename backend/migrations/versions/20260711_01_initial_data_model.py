"""Modelo inicial de dados, posições históricas e previsões."""

import sqlalchemy as sa
from alembic import op

revision = "20260711_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "transit_routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gtfs_route_id", sa.String(100), unique=True),
        sa.Column("short_name", sa.String(50)),
        sa.Column("long_name", sa.String(255)),
    )
    op.create_index("ix_transit_routes_short_name", "transit_routes", ["short_name"])
    op.create_table(
        "route_source_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_code", sa.String(50), nullable=False, unique=True),
        sa.Column("public_line_code", sa.String(50), nullable=False),
        sa.Column("source_name", sa.String(255)),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id")),
    )
    op.create_index(
        "ix_route_source_codes_public_line_code", "route_source_codes", ["public_line_code"]
    )
    op.create_index("ix_route_source_codes_route_id", "route_source_codes", ["route_id"])
    op.create_table(
        "transit_stops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gtfs_stop_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_stop_latitude"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_stop_longitude"),
    )
    op.create_index("ix_transit_stops_coordinates", "transit_stops", ["latitude", "longitude"])
    op.execute(
        "ALTER TABLE transit_stops ADD COLUMN location geography(Point,4326) "
        "GENERATED ALWAYS AS "
        "(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography) STORED"
    )
    op.execute("CREATE INDEX ix_transit_stops_location_gist ON transit_stops USING GIST (location)")
    op.create_table(
        "transit_trips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gtfs_trip_id", sa.String(150), nullable=False, unique=True),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id"), nullable=False),
        sa.Column("service_id", sa.String(100)),
        sa.Column("direction_id", sa.Integer()),
        sa.Column("headsign", sa.String(255)),
        sa.Column("shape_id", sa.String(100)),
    )
    op.create_index("ix_transit_trips_route_id", "transit_trips", ["route_id"])
    op.create_table(
        "trip_stops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("transit_trips.id"), nullable=False),
        sa.Column("stop_id", sa.Integer(), sa.ForeignKey("transit_stops.id"), nullable=False),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("scheduled_arrival_seconds", sa.Integer()),
        sa.Column("scheduled_departure_seconds", sa.Integer()),
        sa.UniqueConstraint("trip_id", "stop_sequence", name="uq_trip_stop_sequence"),
    )
    op.create_index("ix_trip_stops_trip_id", "trip_stops", ["trip_id"])
    op.create_index("ix_trip_stops_stop_id", "trip_stops", ["stop_id"])
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_vehicle_id", sa.String(100), nullable=False, unique=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("disappeared_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_vehicles_last_seen_at", "vehicles", ["last_seen_at"])
    op.create_index("ix_vehicles_is_active", "vehicles", ["is_active"])
    op.create_table(
        "vehicle_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id")),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("transit_trips.id")),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed_kmh", sa.Float()),
        sa.Column("bearing", sa.Float()),
        sa.Column("direction_code", sa.Integer()),
        sa.Column("source_line_code", sa.String(50)),
        sa.Column("distance_traveled", sa.Float()),
        sa.Column("source_event", sa.String(20), nullable=False),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_position_latitude"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_position_longitude"),
        sa.CheckConstraint("speed_kmh IS NULL OR speed_kmh >= 0", name="ck_position_speed"),
        sa.CheckConstraint(
            "bearing IS NULL OR bearing BETWEEN 0 AND 360", name="ck_position_bearing"
        ),
        sa.UniqueConstraint("vehicle_id", "observed_at", name="uq_vehicle_position_observation"),
    )
    for name, columns in (
        ("ix_vehicle_positions_vehicle_id", ["vehicle_id"]),
        ("ix_vehicle_positions_route_id", ["route_id"]),
        ("ix_vehicle_positions_trip_id", ["trip_id"]),
        ("ix_vehicle_positions_observed_at", ["observed_at"]),
        ("ix_vehicle_positions_ingested_at", ["ingested_at"]),
        ("ix_vehicle_positions_source_line_code", ["source_line_code"]),
        ("ix_vehicle_positions_coordinates", ["latitude", "longitude"]),
        ("ix_vehicle_positions_vehicle_observed", ["vehicle_id", "observed_at"]),
        ("ix_vehicle_positions_route_observed", ["route_id", "observed_at"]),
        ("ix_vehicle_positions_trip_observed", ["trip_id", "observed_at"]),
    ):
        op.create_index(name, "vehicle_positions", columns)
    op.execute(
        "ALTER TABLE vehicle_positions ADD COLUMN location geography(Point,4326) "
        "GENERATED ALWAYS AS "
        "(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography) STORED"
    )
    op.execute(
        "CREATE INDEX ix_vehicle_positions_location_gist ON vehicle_positions USING GIST (location)"
    )
    op.execute(
        "CREATE INDEX ix_vehicle_positions_observed_brin "
        "ON vehicle_positions USING BRIN (observed_at)"
    )
    op.create_table(
        "arrival_predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stop_id", sa.Integer(), sa.ForeignKey("transit_stops.id"), nullable=False),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id"), nullable=False),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("transit_trips.id")),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id")),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_arrival", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_arrival", sa.DateTime(timezone=True)),
        sa.Column("distance_to_stop_meters", sa.Float()),
        sa.Column("uncertainty_seconds", sa.Integer()),
        sa.Column("model_version", sa.String(50), nullable=False),
    )
    for column in (
        "stop_id",
        "route_id",
        "trip_id",
        "vehicle_id",
        "generated_at",
        "predicted_arrival",
    ):
        op.create_index(f"ix_arrival_predictions_{column}", "arrival_predictions", [column])
    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("http_status", sa.Integer()),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parsed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parse_error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unmatched_route_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disappeared_vehicle_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_latest_at", sa.DateTime(timezone=True)),
        sa.Column("source_lag_seconds", sa.Float()),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("error_type", sa.String(100)),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_collection_runs_started_at", "collection_runs", ["started_at"])
    op.create_index("ix_collection_runs_status", "collection_runs", ["status"])


def downgrade() -> None:
    op.drop_table("collection_runs")
    op.drop_table("arrival_predictions")
    op.drop_table("vehicle_positions")
    op.drop_table("vehicles")
    op.drop_table("trip_stops")
    op.drop_table("transit_trips")
    op.drop_table("transit_stops")
    op.drop_table("route_source_codes")
    op.drop_table("transit_routes")
