import argparse
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.config import get_settings
from app.database import SessionLocal
from app.models import VehiclePosition
from app.workers.speed_history import refresh_speed_history

logger = logging.getLogger("movepredict.retention")


def delete_expired_positions(*, retention_days: int, batch_size: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    total = 0
    while True:
        with SessionLocal() as session:
            ids = list(
                session.scalars(
                    select(VehiclePosition.id)
                    .where(VehiclePosition.observed_at < cutoff)
                    .order_by(VehiclePosition.observed_at)
                    .limit(batch_size)
                )
            )
            if not ids:
                break
            session.execute(delete(VehiclePosition).where(VehiclePosition.id.in_(ids)))
            session.commit()
            total += len(ids)
        if len(ids) < batch_size:
            break
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplica a retenção do histórico de posições.")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    while True:
        deleted = delete_expired_positions(
            retention_days=settings.position_retention_days,
            batch_size=settings.position_retention_batch_size,
        )
        logger.info("posições removidas pela retenção: %s", deleted)
        history = refresh_speed_history()
        logger.info("estatísticas históricas atualizadas: %s", history["rows_refreshed"])
        if args.once:
            break
        time.sleep(24 * 60 * 60)


if __name__ == "__main__":
    main()
