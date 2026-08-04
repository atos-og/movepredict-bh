"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, LocateFixed, MapPin, Star } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { useVehicles } from "@/hooks/use-realtime";
import { useFavorites } from "@/hooks/use-favorites";
import { useRecentSelections } from "@/hooks/use-recent-selections";
import { api } from "@/lib/api";
import { toRecentLine } from "@/lib/selections";
import type { Line, LineRoute, LineStop } from "@/types/transit";

export function LineDetails({ routeId }: { routeId: string }) {
  const favorites = useFavorites();
  const { remember } = useRecentSelections(20);
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
      remember(toRecentLine(lineResult.data));
      setStops(stopsResult.data);
      setRoute(routeResult.data);
    }).catch(() => {
      if (active) setError("Nao foi possivel carregar esta linha e seu itinerario.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [routeId, direction, remember]);

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
      <h1 className="sr-only">Mapa da linha {line?.route_short_name || routeId}</h1>
      <RoadmapMap lineStops={stops} route={route} vehicles={realtime.vehicles} showVehicles />
      <button className="line-map-back" onClick={() => setMapOpen(false)}><ChevronLeft size={20} />Detalhes</button>
      <section className="bus-map-card"><div><LineBadge value={line?.route_short_name || routeId} /><span><strong>{line?.route_long_name || `Linha ${routeId}`}</strong><small>{realtimeLabel}</small></span></div></section>
    </main>;
  }

  return <main className="roadmap-page line-detail-page">
    <AppHeader title="Detalhes da linha" backHref="/linhas" />
    <section className="line-detail-content">
      <header><LineBadge value={line?.route_short_name || routeId} /><span><h2>{line?.route_long_name || (loading ? "Carregando itinerario" : `Linha ${routeId}`)}</h2><small>Trajeto e paradas oficiais (GTFS)</small></span>{line && <button className="roadmap-icon-button" onClick={() => favorites.toggle(toRecentLine(line))} aria-label={favorites.isFavorite(toRecentLine(line)) ? "Remover linha dos favoritos" : "Adicionar linha aos favoritos"}><Star size={18} fill={favorites.isFavorite(toRecentLine(line)) ? "currentColor" : "none"} /></button>}</header>
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
