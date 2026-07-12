"use client";

import { useEffect, useState } from "react";
import { ChevronRight, LocateFixed, MapPin, X } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useGeolocation } from "@/hooks/use-geolocation";
import { useArrivals } from "@/hooks/use-realtime";
import { api } from "@/lib/api";
import { boundsAround, distanceInMeters, formatDistance, nearestStops } from "@/lib/geo";
import type { Stop } from "@/types/transit";

const PREVIEW_ORIGIN = { latitude: -19.932, longitude: -43.938 };

export function NearbyStops() {
  const geo = useGeolocation();
  const [stops, setStops] = useState<Stop[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "empty" | "error">("loading");
  const [selected, setSelected] = useState<Stop | null>(null);
  const origin = geo.coordinates || PREVIEW_ORIGIN;
  const originLatitude = origin.latitude;
  const originLongitude = origin.longitude;
  const realtime = useArrivals(selected?.stop_id || null);

  useEffect(() => {
    void api.listStopsInBounds(boundsAround({ latitude: originLatitude, longitude: originLongitude }, 1500), 80)
      .then((result) => {
        const nearest = nearestStops(
          { latitude: originLatitude, longitude: originLongitude },
          result.data,
          6,
        );
        setStops(nearest);
        setLoadState(nearest.length ? "ready" : "empty");
      })
      .catch(() => setLoadState("error"));
  }, [originLatitude, originLongitude]);

  return <main className="roadmap-page nearby-page">
    <AppHeader title="Pontos proximos" backHref="/" />
    <section className="nearby-content">
      <header><h1>Pontos proximos</h1><p>Raio de ate 1,5 km</p></header>
      <div className="nearby-map"><RoadmapMap userLocation={origin} nearbyStops={stops} /></div>
      {!geo.coordinates && <button className="nearby-location-request" onClick={geo.requestLocation}><LocateFixed size={16} />Usar minha localizacao</button>}
      {loadState === "loading" && <div className="roadmap-inline-status">Buscando pontos proximos...</div>}
      {loadState === "empty" && <div className="roadmap-inline-status">Nenhum ponto encontrado neste raio.</div>}
      {loadState === "error" && <div className="roadmap-inline-error">Nao foi possivel consultar os pontos.</div>}
      <div className="nearby-cards">{stops.map((stop) => {
        const meters = distanceInMeters(origin, { latitude: stop.stop_lat, longitude: stop.stop_lon });
        return <button className="nearby-stop-card" key={stop.stop_id} onClick={() => setSelected(stop)}><MapPin size={18} /><span><strong>{stop.stop_name}</strong><small>{Math.max(1, Math.round(meters / 80))} min a pe · {formatDistance(meters)}</small><em>Ver chegadas previstas</em></span><ChevronRight size={16} /></button>;
      })}</div>
    </section>
    {selected && <section className="stop-arrivals-sheet" aria-live="polite"><header><span><strong>{selected.stop_name}</strong><small>Ponto {selected.stop_code || selected.stop_id}</small></span><button onClick={() => setSelected(null)} aria-label="Fechar previsoes"><X size={18} /></button></header>{realtime.state === "loading" && <p>Buscando previsoes...</p>}{realtime.state === "offline" && <p>Previsoes temporariamente indisponiveis.</p>}{realtime.state === "empty" && <p>Nenhuma previsao disponivel para este ponto agora.</p>}{realtime.state === "stale" && <p>Ultimas previsoes recebidas; os dados podem estar atrasados.</p>}<ol>{realtime.arrivals.map((arrival) => { const minutes = Math.max(0, Math.ceil((new Date(arrival.predicted_arrival).getTime() - new Date(arrival.generated_at).getTime()) / 60_000)); return <li key={`${arrival.vehicle_id}-${arrival.route_id}-${arrival.predicted_arrival}`}><strong>Linha {arrival.route_id}</strong><span>{minutes <= 1 ? "Chegando" : `${minutes} min`}</span></li>; })}</ol></section>}
    <RoadmapNavigation active="stops" />
  </main>;
}
