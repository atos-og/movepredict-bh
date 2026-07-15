import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal


def build_report(*, days: int = 7, expected_interval_seconds: int = 20) -> dict:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    with SessionLocal() as session:
        collection = (
            session.execute(
                text(
                    """
                WITH ordered AS (
                    SELECT *, started_at - lag(started_at) OVER (ORDER BY started_at) AS gap
                    FROM collection_runs
                    WHERE started_at BETWEEN :start AND :end
                )
                SELECT
                    count(*) AS cycles,
                    count(*) FILTER (WHERE status = 'success') AS successful_cycles,
                    count(*) FILTER (WHERE status = 'failure') AS failed_cycles,
                    min(started_at) AS first_cycle,
                    max(started_at) AS last_cycle,
                    coalesce(sum(parse_error_count), 0) AS parse_errors,
                    coalesce(sum(fetched_count), 0) AS fetched,
                    coalesce(sum(inserted_count), 0) AS inserted,
                    coalesce(sum(duplicate_count), 0) AS duplicates,
                    coalesce(sum(unmatched_route_count), 0) AS unmatched_routes,
                    avg(source_lag_seconds) FILTER (WHERE status = 'success')
                        AS avg_source_lag_seconds,
                    max(source_lag_seconds) AS max_source_lag_seconds,
                    avg(duration_ms) FILTER (WHERE status = 'success') AS avg_duration_ms,
                    count(*) FILTER (WHERE gap > make_interval(secs => :gap_threshold)) AS gaps,
                    coalesce(sum(extract(epoch FROM gap) - :expected_interval)
                        FILTER (WHERE gap > make_interval(secs => :gap_threshold)), 0)
                        AS interior_downtime_seconds
                FROM ordered
                """
                ),
                {
                    "start": start,
                    "end": end,
                    "expected_interval": expected_interval_seconds,
                    "gap_threshold": max(60, expected_interval_seconds * 2),
                },
            )
            .mappings()
            .one()
        )
        positions = (
            session.execute(
                text(
                    """
                SELECT
                    count(*) AS positions,
                    count(DISTINCT vehicle_id) AS vehicles,
                    count(*) FILTER (WHERE route_id IS NOT NULL) AS route_mapped,
                    count(*) FILTER (WHERE trip_id IS NOT NULL) AS trip_matched,
                    count(*) FILTER (WHERE trip_match_method = 'rejected-ambiguous-candidate-v1')
                        AS trip_ambiguous,
                    count(*) FILTER (WHERE trip_match_method = 'rejected-no-confident-candidate-v1')
                        AS trip_no_candidate,
                    count(*) FILTER (WHERE trip_match_method IS NULL) AS trip_not_evaluated,
                    count(*) FILTER (WHERE ingested_at - observed_at > interval '90 seconds')
                        AS delayed_positions,
                    count(*) FILTER (WHERE observed_at > ingested_at + interval '5 minutes')
                        AS future_positions,
                    count(*) FILTER (
                        WHERE latitude NOT BETWEEN -20.1 AND -19.7
                           OR longitude NOT BETWEEN -44.1 AND -43.7
                    ) AS outside_bh_bounds
                FROM vehicle_positions
                WHERE observed_at BETWEEN :start AND :end
                """
                ),
                {"start": start, "end": end},
            )
            .mappings()
            .one()
        )
        latest_vehicles = (
            session.execute(
                text(
                    """
                WITH latest AS (
                    SELECT position.*
                    FROM vehicles AS vehicle
                    CROSS JOIN LATERAL (
                        SELECT route_id, trip_id, trip_match_method, trip_match_confidence
                        FROM vehicle_positions
                        WHERE vehicle_id = vehicle.id
                          AND observed_at BETWEEN :start AND :end
                        ORDER BY observed_at DESC
                        LIMIT 1
                    ) AS position
                )
                SELECT
                    count(*) AS vehicles,
                    count(*) FILTER (WHERE route_id IS NOT NULL) AS route_mapped,
                    count(*) FILTER (WHERE trip_id IS NOT NULL) AS trip_matched,
                    count(*) FILTER (
                        WHERE trip_id IS NOT NULL AND trip_match_confidence >= 0.65
                    ) AS high_confidence,
                    count(*) FILTER (WHERE trip_match_method IS NULL) AS not_evaluated
                FROM latest
                """
                ),
                {"start": start, "end": end},
            )
            .mappings()
            .one()
        )
        lines = list(
            session.execute(
                text(
                    """
                    SELECT
                        coalesce(r.short_name, vp.source_line_code, 'unknown') AS line,
                        count(*) AS positions,
                        count(DISTINCT vp.vehicle_id) AS vehicles,
                        count(*) FILTER (WHERE vp.trip_id IS NOT NULL) AS trip_matched,
                        avg(vp.trip_match_confidence) FILTER (WHERE vp.trip_id IS NOT NULL)
                            AS avg_match_confidence
                    FROM vehicle_positions vp
                    LEFT JOIN transit_routes r ON r.id = vp.route_id
                    WHERE vp.observed_at BETWEEN :start AND :end
                    GROUP BY 1
                    ORDER BY count(*) DESC
                    LIMIT 25
                    """
                ),
                {"start": start, "end": end},
            ).mappings()
        )
        database = list(
            session.execute(
                text(
                    """
                    SELECT
                        relname AS relation,
                        pg_total_relation_size(relid) AS total_bytes,
                        pg_relation_size(relid) AS table_bytes,
                        pg_indexes_size(relid) AS index_bytes,
                        n_live_tup AS estimated_rows,
                        seq_scan,
                        idx_scan
                    FROM pg_stat_user_tables
                    WHERE relname IN (
                        'vehicle_positions', 'arrival_predictions', 'arrival_events',
                        'collection_runs', 'pipeline_runs', 'trip_stops'
                    )
                    ORDER BY pg_total_relation_size(relid) DESC
                    """
                )
            ).mappings()
        )
        eta = (
            session.execute(
                text(
                    """
                SELECT
                    count(*) AS predictions,
                    count(actual_arrival) AS labeled_predictions,
                    count(DISTINCT model_version) AS model_versions,
                    min(generated_at) AS first_prediction,
                    max(generated_at) AS last_prediction
                FROM arrival_predictions
                WHERE generated_at BETWEEN :start AND :end
                """
                ),
                {"start": start, "end": end},
            )
            .mappings()
            .one()
        )
        pipeline = (
            session.execute(
                text(
                    """
                SELECT
                    count(*) AS cycles,
                    count(*) FILTER (WHERE status = 'failure') AS failures,
                    coalesce(sum(positions_inspected), 0) AS positions_inspected,
                    coalesce(sum(positions_matched), 0) AS positions_matched,
                    coalesce(sum(arrivals_detected), 0) AS arrivals_detected,
                    coalesce(sum(predictions_labeled), 0) AS predictions_labeled,
                    coalesce(sum(predictions_created), 0) AS predictions_created,
                    avg(duration_ms) AS avg_duration_ms
                FROM pipeline_runs
                WHERE started_at BETWEEN :start AND :end
                """
                ),
                {"start": start, "end": end},
            )
            .mappings()
            .one()
        )

    collection_dict = _jsonable(collection)
    cycles = collection_dict["cycles"]
    collection_dict["cycle_success_rate"] = (
        collection_dict["successful_cycles"] / cycles if cycles else None
    )
    downtime, availability = _availability_metrics(
        start=start,
        end=end,
        first_cycle=collection["first_cycle"],
        last_cycle=collection["last_cycle"],
        interior_downtime_seconds=float(collection_dict.pop("interior_downtime_seconds") or 0),
    )
    collection_dict["estimated_downtime_seconds"] = downtime
    collection_dict["availability_rate"] = availability
    fetched = collection_dict["fetched"]
    collection_dict["duplicate_rate"] = collection_dict["duplicates"] / fetched if fetched else None
    report = {
        "generated_at": end.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "collection": collection_dict,
        "positions": _with_rates(_jsonable(positions)),
        "latest_vehicles": _vehicle_rates(_jsonable(latest_vehicles)),
        "eta": _jsonable(eta),
        "pipeline": _jsonable(pipeline),
        "top_lines": [_with_rates(_jsonable(row)) for row in lines],
        "database": [_jsonable(row) for row in database],
        "limitations": [
            "Taxas descrevem somente a janela coletada; períodos sem processo ativo "
            "aparecem como gaps.",
            "MAE e percentis só devem ser publicados quando labeled_predictions for suficiente.",
            "Validação de campo exige observação humana e não é inferida automaticamente.",
        ],
    }
    return report


def _with_rates(values: dict) -> dict:
    total = values.get("positions", 0)
    if total:
        for key in ("route_mapped", "trip_matched", "delayed_positions", "outside_bh_bounds"):
            if key in values:
                values[f"{key}_rate"] = values[key] / total
    return values


def _availability_metrics(
    *,
    start: datetime,
    end: datetime,
    first_cycle: datetime | None,
    last_cycle: datetime | None,
    interior_downtime_seconds: float,
) -> tuple[float, float]:
    window_seconds = max(0.0, (end - start).total_seconds())
    if window_seconds == 0:
        return 0.0, 0.0
    if first_cycle is None or last_cycle is None:
        return window_seconds, 0.0
    leading_gap = max(0.0, (first_cycle - start).total_seconds())
    trailing_gap = max(0.0, (end - last_cycle).total_seconds())
    downtime = min(
        window_seconds,
        leading_gap + max(0.0, interior_downtime_seconds) + trailing_gap,
    )
    return downtime, max(0.0, 1 - downtime / window_seconds)


def _vehicle_rates(values: dict) -> dict:
    total = values.get("vehicles", 0)
    if total:
        for key in ("route_mapped", "trip_matched", "high_confidence"):
            values[f"{key}_rate"] = values[key] / total
    return values


def _jsonable(row) -> dict:
    return {
        key: value.isoformat()
        if isinstance(value, datetime)
        else float(value)
        if hasattr(value, "as_integer_ratio") and not isinstance(value, (int, bool))
        else value
        for key, value in dict(row).items()
    }


def render_markdown(report: dict) -> str:
    collection = report["collection"]
    positions = report["positions"]
    latest = report["latest_vehicles"]
    eta = report["eta"]
    pipeline = report.get("pipeline")
    lines = [
        "# Relatório operacional de dados em tempo real",
        "",
        f"Gerado em `{report['generated_at']}` para a janela de {report['window']['days']} dias.",
        "",
        "## Coleta",
        "",
        f"- ciclos: {collection['cycles']} ({collection['successful_cycles']} sucessos, "
        f"{collection['failed_cycles']} falhas);",
        f"- sucesso dos ciclos executados: {_percent(collection['cycle_success_rate'])};",
        f"- disponibilidade temporal observada: {_percent(collection['availability_rate'])};",
        f"- gaps operacionais: {collection['gaps']};",
        f"- indisponibilidade estimada: {round(collection['estimated_downtime_seconds'])} s;",
        f"- lag médio/máximo da fonte: {_number(collection['avg_source_lag_seconds'])} / "
        f"{_number(collection['max_source_lag_seconds'])} s;",
        f"- erros de parse: {collection['parse_errors']}; duplicatas: "
        f"{_percent(collection['duplicate_rate'])}.",
        "",
        "## Qualidade e associação",
        "",
        f"- posições: {positions['positions']}; veículos: {positions['vehicles']};",
        f"- linha GTFS associada: {_percent(positions.get('route_mapped_rate'))};",
        f"- viagem associada: {_percent(positions.get('trip_matched_rate'))};",
        f"- veículos com última posição associada: {latest['trip_matched']}/"
        f"{latest['vehicles']} ({_percent(latest.get('trip_matched_rate'))});",
        f"- posições ainda não avaliadas: {positions['trip_not_evaluated']};",
        f"- atrasadas >90 s: {positions['delayed_positions']}; fora do envelope de BH: "
        f"{positions['outside_bh_bounds']}.",
        f"- posições mais de 5 min no futuro: {positions['future_positions']}.",
        "",
        "## ETA",
        "",
        f"- previsões: {eta['predictions']}; chegadas reais rotuladas: "
        f"{eta['labeled_predictions']};",
        "- MAE, mediana, P90 e P95 permanecem não publicáveis enquanto não houver "
        "amostra rotulada.",
        "",
    ]
    if pipeline:
        lines.extend(
            [
                "## Pipeline",
                "",
                f"- ciclos: {pipeline['cycles']}; falhas: {pipeline['failures']};",
                f"- matching: {pipeline['positions_matched']}/"
                f"{pipeline['positions_inspected']}; chegadas: {pipeline['arrivals_detected']};",
                f"- previsões criadas/rotuladas: {pipeline['predictions_created']}/"
                f"{pipeline['predictions_labeled']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Banco",
            "",
            "| relação | linhas estimadas | total | tabela | índices |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for relation in report["database"]:
        lines.append(
            f"| {relation['relation']} | {relation['estimated_rows']} | "
            f"{_bytes(relation['total_bytes'])} | {_bytes(relation['table_bytes'])} | "
            f"{_bytes(relation['index_bytes'])} |"
        )
    lines.extend(
        [
            "",
            "## Limitações",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
        ]
    )
    return "\n".join(lines)


def _percent(value) -> str:
    return "N/A" if value is None else f"{value * 100:.2f}%"


def _number(value) -> str:
    return "N/A" if value is None else f"{value:.2f}"


def _bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{number:.1f} {unit}"
        number /= 1024
    return f"{number:.1f} TiB"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audita fonte, matching, ETA e PostgreSQL.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = build_report(days=args.days)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(payload + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(payload)


if __name__ == "__main__":
    main()
