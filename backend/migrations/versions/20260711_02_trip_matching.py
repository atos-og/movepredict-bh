"""Dados de calendário, shapes, associação de viagens e chegadas."""

import sqlalchemy as sa
from alembic import op

revision = "20260711_02"
down_revision = "20260711_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transit_trips", sa.Column("start_time_seconds", sa.Integer()))
    op.add_column("transit_trips", sa.Column("end_time_seconds", sa.Integer()))
    op.create_index("ix_transit_trips_start_time_seconds", "transit_trips", ["start_time_seconds"])
    op.add_column("trip_stops", sa.Column("shape_progress", sa.Float()))
    op.add_column("vehicle_positions", sa.Column("shape_progress", sa.Float()))
    op.add_column("vehicle_positions", sa.Column("trip_match_confidence", sa.Float()))
    op.add_column("vehicle_positions", sa.Column("trip_match_method", sa.String(50)))
    op.create_table(
        "service_calendars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.String(100), nullable=False, unique=True),
        sa.Column("monday", sa.Boolean(), nullable=False),
        sa.Column("tuesday", sa.Boolean(), nullable=False),
        sa.Column("wednesday", sa.Boolean(), nullable=False),
        sa.Column("thursday", sa.Boolean(), nullable=False),
        sa.Column("friday", sa.Boolean(), nullable=False),
        sa.Column("saturday", sa.Boolean(), nullable=False),
        sa.Column("sunday", sa.Boolean(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
    )
    op.create_table(
        "service_exceptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.String(100), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("exception_type", sa.Integer(), nullable=False),
        sa.UniqueConstraint("service_id", "service_date", name="uq_service_exception"),
        sa.CheckConstraint("exception_type IN (1, 2)", name="ck_service_exception_type"),
    )
    op.create_index("ix_service_exceptions_service_id", "service_exceptions", ["service_id"])
    op.create_index("ix_service_exceptions_service_date", "service_exceptions", ["service_date"])
    op.create_table(
        "transit_shapes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gtfs_shape_id", sa.String(100), nullable=False, unique=True),
        sa.Column("point_count", sa.Integer(), nullable=False),
        sa.Column("length_meters", sa.Float()),
    )
    op.execute("ALTER TABLE transit_shapes ADD COLUMN path geometry(LineString,4326) NOT NULL")
    op.execute("CREATE INDEX ix_transit_shapes_path_gist ON transit_shapes USING GIST (path)")
    op.create_table(
        "arrival_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("transit_routes.id"), nullable=False),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("transit_trips.id"), nullable=False),
        sa.Column("stop_id", sa.Integer(), sa.ForeignKey("transit_stops.id"), nullable=False),
        sa.Column(
            "position_id", sa.Integer(), sa.ForeignKey("vehicle_positions.id"), nullable=False
        ),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("distance_to_stop_meters", sa.Float(), nullable=False),
        sa.Column("detection_method", sa.String(50), nullable=False),
        sa.UniqueConstraint("position_id"),
        sa.UniqueConstraint(
            "vehicle_id",
            "trip_id",
            "stop_id",
            "service_date",
            name="uq_arrival_event_vehicle_trip_stop_date",
        ),
        sa.CheckConstraint("distance_to_stop_meters >= 0", name="ck_arrival_distance"),
    )
    for column in ("vehicle_id", "route_id", "trip_id", "stop_id", "service_date", "arrived_at"):
        op.create_index(f"ix_arrival_events_{column}", "arrival_events", [column])


def downgrade() -> None:
    op.drop_table("arrival_events")
    op.drop_table("transit_shapes")
    op.drop_table("service_exceptions")
    op.drop_table("service_calendars")
    op.drop_column("vehicle_positions", "trip_match_method")
    op.drop_column("vehicle_positions", "trip_match_confidence")
    op.drop_column("vehicle_positions", "shape_progress")
    op.drop_column("trip_stops", "shape_progress")
    op.drop_index("ix_transit_trips_start_time_seconds", table_name="transit_trips")
    op.drop_column("transit_trips", "end_time_seconds")
    op.drop_column("transit_trips", "start_time_seconds")
