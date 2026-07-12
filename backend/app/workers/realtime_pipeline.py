import argparse
import json
import logging
import time
from dataclasses import asdict

from app.config import get_settings
from app.database import SessionLocal
from app.services.arrival_detection import detect_arrivals
from app.services.prediction_generation import generate_predictions
from app.services.trip_matching import match_unassigned_positions
from app.workers.realtime_consumer import collect_once

logger = logging.getLogger("movepredict.pipeline")


def run_pipeline_once() -> dict:
    settings = get_settings()
    collection = collect_once()
    with SessionLocal() as session:
        matching = match_unassigned_positions(session, limit=settings.trip_match_batch_size)
        arrivals = detect_arrivals(session, limit=settings.arrival_detection_batch_size)
        predictions = generate_predictions(session)
    result = {
        "collection": asdict(collection),
        "matching": asdict(matching),
        "arrivals": asdict(arrivals),
        "predictions": asdict(predictions),
    }
    logger.info(json.dumps({"event": "pipeline_success", **result}, default=str))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa coleta, matching, chegada e ETA.")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    while True:
        started = time.monotonic()
        try:
            run_pipeline_once()
        except Exception:
            logger.exception("pipeline_failure")
            if args.once:
                raise
        if args.once:
            break
        elapsed = time.monotonic() - started
        time.sleep(max(0, settings.realtime_interval_seconds - elapsed))


if __name__ == "__main__":
    main()
