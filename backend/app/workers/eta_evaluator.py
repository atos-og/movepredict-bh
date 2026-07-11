import argparse
import json
from dataclasses import asdict

from app.database import SessionLocal
from app.services.eta import (
    calculate_metrics,
    load_evaluation_records,
    segmented_metrics,
    temporal_split,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o ETA sem vazamento temporal.")
    parser.add_argument("--model-version", default="baseline-schedule-v1")
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    args = parser.parse_args()
    with SessionLocal() as session:
        records = load_evaluation_records(session, args.model_version)
    train, validation = temporal_split(records, args.validation_fraction)
    metrics = calculate_metrics(validation)
    payload = {
        "model_version": args.model_version,
        "train_count": len(train),
        "validation_count": len(validation),
        "validation_start": validation[0].generated_at.isoformat() if validation else None,
        "overall": asdict(metrics) if metrics else None,
        "segments": {
            dimension: {key: asdict(value) for key, value in groups.items()}
            for dimension, groups in segmented_metrics(validation).items()
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
