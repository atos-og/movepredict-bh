from app.workers.operational_report import _vehicle_rates, _with_rates, render_markdown


def test_quality_rates_and_markdown_rendering() -> None:
    positions = _with_rates(
        {
            "positions": 100,
            "route_mapped": 90,
            "trip_matched": 40,
            "delayed_positions": 2,
            "outside_bh_bounds": 1,
        }
    )
    assert positions["route_mapped_rate"] == 0.9
    assert positions["trip_matched_rate"] == 0.4
    latest = _vehicle_rates(
        {"vehicles": 20, "route_mapped": 18, "trip_matched": 10, "high_confidence": 8}
    )
    assert latest["trip_matched_rate"] == 0.5

    report = {
        "generated_at": "2026-07-14T12:00:00+00:00",
        "window": {"days": 7},
        "collection": {
            "cycles": 10,
            "successful_cycles": 9,
            "failed_cycles": 1,
            "success_rate": 0.9,
            "gaps": 1,
            "estimated_downtime_seconds": 60,
            "avg_source_lag_seconds": 2.0,
            "max_source_lag_seconds": 5.0,
            "parse_errors": 0,
            "duplicate_rate": 0.1,
        },
        "positions": {
            **positions,
            "vehicles": 20,
            "trip_not_evaluated": 50,
        },
        "eta": {"predictions": 10, "labeled_predictions": 5},
        "pipeline": {
            "cycles": 2,
            "failures": 0,
            "positions_inspected": 100,
            "positions_matched": 40,
            "arrivals_detected": 5,
            "predictions_created": 20,
            "predictions_labeled": 3,
        },
        "latest_vehicles": {**latest, "not_evaluated": 2},
        "database": [],
        "limitations": ["Teste"],
    }
    markdown = render_markdown(report)
    assert "90.00%" in markdown
    assert "chegadas reais rotuladas: 5" in markdown
