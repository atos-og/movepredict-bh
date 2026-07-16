"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, LocateFixed, MapPin } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { useVehicles } from "@/hooks/use-realtime";
import { api } from "@/lib/api";
import type { Line, LineRoute, LineStop } from "@/types/transit";

export function LineDetails({ routeId }: { routeId: string }) {
  const [line, setLine] = useState<Line | null>(null);
  const [stops, setStops] = useState<LineStop[]>([]);
  const [route, setRoute] = useState<LineRoute | null>(null);
  const [direction, setDirection] = useState<string | undefined>();
  const [availableDirections, setAvailableDirections] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapOpen, setMapOpen] = useState(false);
  const realtime = useVehicles(routeId);

  function changeDirection(value: string) {
    if (value === direction) return;
    setLoading(true);
    setError(null);
    setDirection(value);
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      api.listLineTrips(routeId, "0", 1),
      api.listLineTrips(routeId, "1", 1),
    ]).then(([outbound, inbound]) => {
      if (!active) return;
      setAvailableDirections([
        ...(outbound.meta.total > 0 ? ["0"] : []),
        ...(inbound.meta.total > 0 ? ["1"] : []),
      ]);
    }).catch(() => {
      if (active) setAvailableDirections([]);
    });
    return () => { active = false; };
  }, [routeId]);

  useEffect(() => {
    let active = true;
    Promise.all([
      api.getLine(routeId),
      api.getLineStops(routeId, direction),
      api.getLineRoute(routeId, direction),
    ]).then(([lineResult, stopsResult, routeResult]) => {
      if (!active) return;
      setLine(lineResult.data);
      setStops(stopsResult.data);
      setRoute(routeResult.data);
    }).catch(() => {
      if (active) setError("Nao foi possivel carregar esta linha e seu itinerario.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [routeId, direction]);

  const realtimeLabel = realtime.state === "live"
    ? `${realtime.vehicles.length} veiculo(s) atualizado(s) automaticamente`
    : realtime.state === "stale"
      ? "Posicoes recebidas, mas desatualizadas"
      : realtime.state === "loading"
        ? "Buscando veiculos ativos..."
      : realtime.message || "Nenhum veiculo ativo para esta linha agora";
  const displayedDirection = direction ?? route?.direction_id;

  if (mapOpen) {
    return <main className="roadmap-page bus-map-page">
      <RoadmapMap lineStops={stops} route={route} vehicles={realtime.vehicles} showVehicles />
      <button className="line-map-back" onClick={() => setMapOpen(false)}><ChevronLeft size={20} />Detalhes</button>
      <section className="bus-map-card"><div><LineBadge value={line?.route_short_name || routeId} /><span><strong>{line?.route_long_name || `Linha ${routeId}`}</strong><small>{realtimeLabel}</small></span></div></section>
    </main>;
  }

  return <main className="roadmap-page line-detail-page">
    <AppHeader title="Detalhes da linha" backHref="/linhas" />
    <section className="line-detail-content">
      <header><LineBadge value={line?.route_short_name || routeId} /><span><strong>{line?.route_long_name || (loading ? "Carregando itinerario" : `Linha ${routeId}`)}</strong><small>Trajeto e paradas oficiais (GTFS)</small></span></header>
      {availableDirections.length > 1 && <div className="roadmap-direction-tabs">{availableDirections.includes("0") && <button className={displayedDirection === "0" ? "active" : ""} onClick={() => changeDirection("0")}>Ida</button>}{availableDirections.includes("1") && <button className={displayedDirection === "1" ? "active" : ""} onClick={() => changeDirection("1")}>Volta</button>}</div>}
      <div className="line-location-note"><LocateFixed size={16} /><span><strong>Monitoramento da linha</strong><small>{realtimeLabel}</small></span></div>
      {error && <div className="roadmap-inline-error">{error}</div>}
      <div className="stop-timeline" aria-busy={loading}>{loading
        ? Array.from({ length: 8 }).map((_, index) => <span className="roadmap-list-skeleton" key={index} />)
        : stops.map((stop, index) => <div className={index === Math.floor(stops.length / 2) ? "selected" : ""} key={`${stop.stop_id}-${stop.stop_sequence}`}><i /><span><strong>{stop.stop_name}</strong><small>{stop.departure_time ? `Programado ${stop.departure_time.slice(0, 5)}` : `Ponto ${stop.stop_code || stop.stop_id}`}</small></span></div>)}</div>
    </section>
    <button className="roadmap-primary route-bottom-action" disabled={!route} onClick={() => setMapOpen(true)}><MapPin size={17} />Ver no mapa</button>
  </main>;
}
