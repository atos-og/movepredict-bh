"use client";

import { useEffect, useState } from "react";
import { ChevronRight, LocateFixed, MapPin } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useGeolocation } from "@/hooks/use-geolocation";
import { api } from "@/lib/api";
import { boundsAround, distanceInMeters, formatDistance, nearestStops } from "@/lib/geo";
import type { Stop } from "@/types/transit";

const PREVIEW_ORIGIN = { latitude: -19.932, longitude: -43.938 };

export function NearbyStops() {
  const geo = useGeolocation();
  const [stops, setStops] = useState<Stop[]>([]);
  const origin = geo.coordinates || PREVIEW_ORIGIN;

  useEffect(() => { void api.listStopsInBounds(boundsAround(origin, 1500), 80).then((result) => setStops(nearestStops(origin, result.data, 3))).catch(() => setStops([])); }, [origin]);

  return <main className="roadmap-page nearby-page"><AppHeader title="Pontos próximos" backHref="/" /><section className="nearby-content"><header><h1>Pontos próximos</h1><p>Raio de até 1,5 km</p></header><div className="nearby-map"><RoadmapMap userLocation={origin} nearbyStops={stops} /></div>{!geo.coordinates && <button className="nearby-location-request" onClick={geo.requestLocation}><LocateFixed size={16} />Usar minha localização</button>}<div className="nearby-cards">{stops.map((stop) => { const meters = distanceInMeters(origin, { latitude: stop.stop_lat, longitude: stop.stop_lon }); return <article key={stop.stop_id}><MapPin size={18} /><span><strong>{stop.stop_name}</strong><small>{Math.max(1, Math.round(meters / 80))} min a pé · {formatDistance(meters)}</small><em>Linhas deste ponto indisponíveis na API atual</em></span><ChevronRight size={16} /></article>; })}</div></section><RoadmapNavigation active="stops" /></main>;
}
