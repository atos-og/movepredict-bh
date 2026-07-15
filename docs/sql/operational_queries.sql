-- Veículos ativos: view estável criada pela migration 20260714_03.
SELECT *
FROM current_vehicle_positions
WHERE observed_at >= now() - interval '2 minutes'
ORDER BY observed_at DESC;

-- Previsões atuais por ponto GTFS.
SELECT *
FROM current_arrival_predictions
WHERE stop_id = :'stop_id'
ORDER BY predicted_arrival;

-- Disponibilidade e qualidade da fonte nas últimas 24 horas.
SELECT
    count(*) AS cycles,
    count(*) FILTER (WHERE status = 'success') AS successes,
    count(*) FILTER (WHERE status = 'failure') AS failures,
    round(avg(source_lag_seconds)::numeric, 2) AS avg_lag_seconds,
    max(source_lag_seconds) AS max_lag_seconds,
    sum(parse_error_count) AS parse_errors
FROM collection_runs
WHERE started_at >= now() - interval '24 hours';

-- Cobertura do matching por linha nas últimas 24 horas.
SELECT
    coalesce(route.short_name, position.source_line_code) AS line,
    count(*) AS positions,
    count(*) FILTER (WHERE position.trip_id IS NOT NULL) AS matched,
    round(
        100.0 * count(*) FILTER (WHERE position.trip_id IS NOT NULL) / nullif(count(*), 0),
        2
    ) AS matched_percent
FROM vehicle_positions position
LEFT JOIN transit_routes route ON route.id = position.route_id
WHERE position.observed_at >= now() - interval '24 hours'
GROUP BY 1
ORDER BY positions DESC;

-- Crescimento e peso das principais tabelas.
SELECT
    relname,
    n_live_tup AS estimated_rows,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_indexes_size(relid)) AS index_size,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
