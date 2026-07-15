import argparse
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.database import SessionLocal
from app.services.trip_matching import match_unassigned_positions


def backfill(*, hours: int, limit_total: int, batch_size: int) -> dict:
    since = datetime.now(UTC) - timedelta(hours=hours)
    with SessionLocal() as session:
        reset = session.execute(
            text(
                """
                WITH candidates AS (
                    SELECT id
                    FROM vehicle_positions
                    WHERE observed_at >= :since
                      AND trip_id IS NULL
                      AND route_id IS NOT NULL
                      AND trip_match_method LIKE 'rejected-%'
                    ORDER BY observed_at DESC
                    LIMIT :limit_total
                )
                UPDATE vehicle_positions AS position
                SET trip_match_method = NULL, trip_match_confidence = NULL
                FROM candidates
                WHERE position.id = candidates.id
                """
            ),
            {"since": since, "limit_total": limit_total},
        ).rowcount
        session.commit()
        inspected = matched = no_candidate = ambiguous = 0
        while inspected < limit_total:
            result = match_unassigned_positions(
                session, limit=min(batch_size, limit_total - inspected)
            )
            if result.inspected == 0:
                break
            inspected += result.inspected
            matched += result.matched
            no_candidate += result.rejected_no_candidate
            ambiguous += result.rejected_ambiguous
    return {
        "since": since.isoformat(),
        "reset": reset,
        "inspected": inspected,
        "matched": matched,
        "rejected_no_candidate": no_candidate,
        "rejected_ambiguous": ambiguous,
        "match_rate": matched / inspected if inspected else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reprocessa matching após atualização do GTFS.")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--limit-total", type=int, default=10_000)
    parser.add_argument("--batch-size", type=int, default=250)
    args = parser.parse_args()
    print(
        json.dumps(
            backfill(
                hours=args.hours,
                limit_total=args.limit_total,
                batch_size=args.batch_size,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
