import argparse
import json
from dataclasses import asdict
from pathlib import Path

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
    parser.add_argument("--minimum-validation-samples", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with SessionLocal() as session:
        records = load_evaluation_records(session, args.model_version)
    train, validation = temporal_split(records, args.validation_fraction)
    publishable = len(validation) >= args.minimum_validation_samples
    metrics = calculate_metrics(validation) if publishable else None
    payload = {
        "model_version": args.model_version,
        "train_count": len(train),
        "validation_count": len(validation),
        "validation_start": validation[0].generated_at.isoformat() if validation else None,
        "minimum_validation_samples": args.minimum_validation_samples,
        "publishable": publishable,
        "not_publishable_reason": None
        if publishable
        else "Amostra temporal rotulada abaixo do mínimo configurado.",
        "overall": asdict(metrics) if metrics else None,
        "segments": {
            dimension: {key: asdict(value) for key, value in groups.items()}
            for dimension, groups in segmented_metrics(
                validation, min_samples=args.minimum_validation_samples
            ).items()
        },
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
