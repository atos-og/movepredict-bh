"use client";

import { useEffect, useState } from "react";
import { ChevronRight, LocateFixed, MapPin, Search, X } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useGeolocation } from "@/hooks/use-geolocation";
import { useArrivals } from "@/hooks/use-realtime";
import { api } from "@/lib/api";
import { boundsAround, distanceInMeters, formatDistance, nearestStops } from "@/lib/geo";
import type { Stop } from "@/types/transit";

type LoadState = "idle" | "loading" | "ready" | "empty" | "error";

export function NearbyStops() {
  const geo = useGeolocation();
  const [stops, setStops] = useState<Stop[]>([]);
  const [query, setQuery] = useState("");
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [selected, setSelected] = useState<Stop | null>(null);
  const [routeLabels, setRouteLabels] = useState<Record<string, string>>({});
  const origin = geo.coordinates;
  const realtime = useArrivals(selected?.stop_id || null);

  useEffect(() => {
    let active = true;
    const normalizedQuery = query.trim();
    if (normalizedQuery.length < 2 && !origin) {
      queueMicrotask(() => {
        if (!active) return;
        setStops([]);
        setLoadState("idle");
      });
      return () => {
        active = false;
      };
    }

    const timer = window.setTimeout(() => {
      setLoadState("loading");
      const request = normalizedQuery.length >= 2
        ? api.listStops(normalizedQuery, 30)
        : api.listStopsInBounds(boundsAround(origin!, 1500), 80);
      void request
        .then((result) => {
          if (!active) return;
          const items = origin
            ? nearestStops(origin, result.data, normalizedQuery.length >= 2 ? 30 : 6)
            : result.data;
          setStops(items);
          setLoadState(items.length ? "ready" : "empty");
        })
        .catch(() => {
          if (active) setLoadState("error");
        });
    }, normalizedQuery.length >= 2 ? 250 : 0);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [origin, query]);

  useEffect(() => {
    const missingRouteIds = [...new Set(realtime.arrivals.map((arrival) => arrival.route_id))]
      .filter((routeId) => !routeLabels[routeId]);
    if (!missingRouteIds.length) return;
    let active = true;
    void Promise.allSettled(missingRouteIds.map((routeId) => api.getLine(routeId))).then(
      (results) => {
        if (!active) return;
        setRouteLabels((current) => {
          const next = { ...current };
          results.forEach((result, index) => {
            if (result.status === "fulfilled") {
              next[missingRouteIds[index]] =
                result.value.data.route_short_name || missingRouteIds[index];
            }
          });
          return next;
        });
      },
    );
    return () => {
      active = false;
    };
  }, [realtime.arrivals, routeLabels]);

  return (
    <main className="roadmap-page nearby-page">
      <AppHeader title={origin ? "Pontos proximos" : "Encontrar pontos"} backHref="/" />
      <section className="nearby-content">
        <header>
          <h1>{origin ? "Pontos proximos" : "Encontre um ponto"}</h1>
          <p>{origin ? "Raio de ate 1,5 km" : "Dados oficiais da PBH"}</p>
        </header>
        <div className="nearby-map">
          <RoadmapMap userLocation={origin} nearbyStops={stops} />
        </div>
        <label className="list-search">
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar ponto ou endereco"
          />
          {query && (
            <button type="button" onClick={() => setQuery("")} aria-label="Limpar busca">
              <X size={16} />
            </button>
          )}
        </label>
        {!origin && (
          <button className="nearby-location-request" onClick={geo.requestLocation}>
            <LocateFixed size={16} />Usar minha localizacao
          </button>
        )}
        {loadState === "idle" && (
          <div className="roadmap-inline-status">
            Use sua localizacao ou busque um ponto pelo nome.
          </div>
        )}
        {loadState === "loading" && (
          <div className="roadmap-inline-status">Buscando pontos...</div>
        )}
        {loadState === "empty" && (
          <div className="roadmap-inline-status">Nenhum ponto encontrado.</div>
        )}
        {loadState === "error" && (
          <div className="roadmap-inline-error">Nao foi possivel consultar os pontos.</div>
        )}
        <div className="nearby-cards">
          {stops.map((stop) => {
            const meters = origin
              ? distanceInMeters(origin, {
                  latitude: stop.stop_lat,
                  longitude: stop.stop_lon,
                })
              : null;
            const distanceLabel = meters === null
              ? `Ponto ${stop.stop_code || stop.stop_id}`
              : `${Math.max(1, Math.round(meters / 80))} min a pe - ${formatDistance(meters)}`;
            return (
              <button
                className="nearby-stop-card"
                key={stop.stop_id}
                onClick={() => setSelected(stop)}
              >
                <MapPin size={18} />
                <span>
                  <strong>{stop.stop_name}</strong>
                  <small>{distanceLabel}</small>
                  <em>Ver chegadas previstas</em>
                </span>
                <ChevronRight size={16} />
              </button>
            );
          })}
        </div>
      </section>
      {selected && (
        <section className="stop-arrivals-sheet" aria-live="polite">
          <header>
            <span>
              <strong>{selected.stop_name}</strong>
              <small>Ponto {selected.stop_code || selected.stop_id}</small>
            </span>
            <button onClick={() => setSelected(null)} aria-label="Fechar previsoes">
              <X size={18} />
            </button>
          </header>
          {realtime.state === "loading" && <p>Buscando previsoes...</p>}
          {realtime.state === "offline" && <p>Previsoes temporariamente indisponiveis.</p>}
          {realtime.state === "empty" && (
            <p>Nenhuma previsao disponivel para este ponto agora.</p>
          )}
          {realtime.state === "stale" && (
            <p>Ultimas previsoes recebidas; os dados podem estar atrasados.</p>
          )}
          <ol>
            {realtime.arrivals.map((arrival) => {
              const referenceTime = realtime.meta?.generated_at || arrival.generated_at;
              const minutes = Math.max(
                0,
                Math.ceil(
                  (new Date(arrival.predicted_arrival).getTime()
                    - new Date(referenceTime).getTime())
                    / 60_000,
                ),
              );
              return (
                <li key={`${arrival.vehicle_id}-${arrival.route_id}-${arrival.predicted_arrival}`}>
                  <strong>Linha {routeLabels[arrival.route_id] || arrival.route_id}</strong>
                  <span>{minutes <= 1 ? "Chegando" : `${minutes} min`}</span>
                </li>
              );
            })}
          </ol>
        </section>
      )}
      <RoadmapNavigation active="stops" />
    </main>
  );
}
