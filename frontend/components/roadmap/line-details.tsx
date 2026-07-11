"use client";
import { useEffect, useState } from "react";
import { ChevronLeft, LocateFixed, MapPin } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { api } from "@/lib/api";
import type { Line, LineRoute, LineStop } from "@/types/transit";

export function LineDetails({ routeId }: { routeId: string }) {
  const [line, setLine] = useState<Line | null>(null);
  const [stops, setStops] = useState<LineStop[]>([]);
  const [route, setRoute] = useState<LineRoute | null>(null);
  const [direction, setDirection] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapOpen, setMapOpen] = useState(false);

  useEffect(() => {
    let active = true;
    void api.getLine(routeId).then((result) => { if (active) setLine(result.data); }).catch(() => { if (active) setError("Esta linha não foi encontrada na base GTFS atual."); });
    void api.getLineStops(routeId, direction).then((result) => { if (active) setStops(result.data); }).catch(() => { if (active) setError("Não foi possível carregar os pontos desta linha."); }).finally(() => { if (active) setLoading(false); });
    void api.getLineRoute(routeId, direction).then((result) => { if (active) setRoute(result.data); }).catch(() => { if (active) setRoute(null); });
    return () => { active = false; };
  }, [routeId, direction]);

  function changeDirection(value: string) { if (value === direction) return; setLoading(true); setError(null); setDirection(value); }

  if (mapOpen) return <main className="roadmap-page bus-map-page"><RoadmapMap lineStops={stops} route={route} /><button className="line-map-back" onClick={() => setMapOpen(false)}><ChevronLeft size={20} />Detalhes</button><section className="bus-map-card"><div><LineBadge value={line?.route_short_name || routeId} /><span><strong>{line?.route_long_name || `Linha ${routeId}`}</strong><small>Trajeto oficial programado</small></span></div></section></main>;
  return <main className="roadmap-page line-detail-page"><AppHeader title="Detalhes da linha" backHref="/linhas" /><section className="line-detail-content"><header><LineBadge value={line?.route_short_name || routeId} /><span><strong>{line?.route_long_name || (loading ? "Carregando itinerário" : `Linha ${routeId}`)}</strong><small>Trajeto e paradas oficiais (GTFS)</small></span></header><div className="roadmap-direction-tabs"><button className={direction === "0" ? "active" : ""} onClick={() => changeDirection("0")}>Ida</button><button className={direction === "1" ? "active" : ""} onClick={() => changeDirection("1")}>Volta</button></div><div className="line-location-note"><LocateFixed size={16} /><span><strong>Usar minha localização</strong><small>Horários ao vivo ainda não disponíveis</small></span></div>{error && <div className="roadmap-inline-error">{error}</div>}<div className="stop-timeline" aria-busy={loading}>{loading ? Array.from({ length: 8 }).map((_, index) => <span className="roadmap-list-skeleton" key={index} />) : stops.map((stop, index) => <div className={index === Math.floor(stops.length / 2) ? "selected" : ""} key={`${stop.stop_id}-${stop.stop_sequence}`}><i /><span><strong>{stop.stop_name}</strong><small>{stop.departure_time ? `Programado ${stop.departure_time.slice(0, 5)}` : `Ponto ${stop.stop_code || stop.stop_id}`}</small></span></div>)}</div></section><button className="roadmap-primary route-bottom-action" disabled={!route} onClick={() => setMapOpen(true)}><MapPin size={17} />Ver no mapa</button></main>;
}
