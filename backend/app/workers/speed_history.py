import argparse
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.database import SessionLocal


def refresh_speed_history(*, days: int = 28) -> dict:
    window_end = datetime.now(UTC)
    window_start = window_end - timedelta(days=days)
    with SessionLocal() as session:
        result = session.execute(
            text(
                """
                INSERT INTO route_hour_speed_stats (
                    route_id, local_hour, average_speed_kmh, sample_size,
                    window_start, window_end, refreshed_at
                )
                SELECT
                    route_id,
                    EXTRACT(HOUR FROM observed_at AT TIME ZONE 'America/Sao_Paulo')::integer,
                    avg(speed_kmh),
                    count(*),
                    :window_start,
                    :window_end,
                    :window_end
                FROM vehicle_positions
                WHERE route_id IS NOT NULL
                  AND speed_kmh BETWEEN 5 AND 90
                  AND observed_at BETWEEN :window_start AND :window_end
                GROUP BY route_id, 2
                ON CONFLICT (route_id, local_hour) DO UPDATE SET
                    average_speed_kmh = EXCLUDED.average_speed_kmh,
                    sample_size = EXCLUDED.sample_size,
                    window_start = EXCLUDED.window_start,
                    window_end = EXCLUDED.window_end,
                    refreshed_at = EXCLUDED.refreshed_at
                """
            ),
            {"window_start": window_start, "window_end": window_end},
        )
        session.commit()
    return {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "rows_refreshed": result.rowcount,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza velocidade histórica por linha/hora.")
    parser.add_argument("--days", type=int, default=28)
    args = parser.parse_args()
    print(json.dumps(refresh_speed_history(days=args.days), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
