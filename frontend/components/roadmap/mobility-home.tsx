"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ChevronRight, Clock3, LocateFixed, MapPin, Search, X } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LocationLoadingSheet } from "@/components/roadmap/location-loading-sheet";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useGeolocation } from "@/hooks/use-geolocation";
import { useRecentSelections } from "@/hooks/use-recent-selections";
import { api } from "@/lib/api";
import { boundsAround, nearestStops } from "@/lib/geo";
import type { Stop } from "@/types/transit";

type HomeScreen = "home" | "permission" | "loading" | "ready" | "search";
const developmentPlaces = ["Savassi", "Praça Diogo de Vasconcelos", "Shopping Pátio Savassi", "Av. Cristóvão Colombo"];

export function MobilityHome() {
  const params = useSearchParams();
  const requestedScreen = params.get("screen") as HomeScreen | null;
  const [screen, setScreen] = useState<HomeScreen>(requestedScreen || "home");
  const [query, setQuery] = useState("");
  const [nearby, setNearby] = useState<Stop[]>([]);
  const geolocation = useGeolocation();
  const recent = useRecentSelections();

  useEffect(() => {
    if (!geolocation.coordinates) return;
    void api.listStopsInBounds(boundsAround(geolocation.coordinates, 1500), 60).then((result) => setNearby(nearestStops(geolocation.coordinates!, result.data, 3))).catch(() => setNearby([]));
  }, [geolocation.coordinates]);

  useEffect(() => {
    if (geolocation.status !== "granted") return;
    const timer = window.setTimeout(() => setScreen("ready"), 0);
    return () => window.clearTimeout(timer);
  }, [geolocation.status]);

  const previewCoordinates = requestedScreen === "ready" || requestedScreen === "loading" ? { latitude: -19.932, longitude: -43.938 } : null;
  const mapCoordinates = geolocation.coordinates || previewCoordinates;

  function requestLocation() {
    setScreen("loading");
    geolocation.requestLocation();
  }

  if (screen === "search") return <DestinationSearchScreen value={query} onChange={setQuery} onCancel={() => { setQuery(""); setScreen(mapCoordinates ? "ready" : "home"); }} />;

  return (
    <main className="roadmap-app">
      <AppHeader />
      <RoadmapMap userLocation={mapCoordinates} nearbyStops={nearby} />
      {screen === "permission" && <section className="roadmap-permission"><span><LocateFixed size={30} /></span><h1>Encontre a melhor rota saindo de onde você está</h1><p>Usaremos sua localização apenas para encontrar o ponto mais próximo e calcular sua viagem.</p><button className="roadmap-primary" onClick={requestLocation}><LocateFixed size={18} />Usar minha localização</button><button className="roadmap-text-button" onClick={() => setScreen("home")}>Agora não</button></section>}
      {screen === "loading" && <><div className="location-pulse" aria-hidden="true"><i /></div><LocationLoadingSheet /></>}
      {(screen === "home" || screen === "ready") && <HomeCard ready={screen === "ready"} nearby={nearby} recent={recent.items} onSearch={() => setScreen("search")} onLocation={() => setScreen("permission")} />}
      {screen !== "loading" && <RoadmapNavigation active="home" />}
    </main>
  );
}

function HomeCard({ ready, nearby, recent, onSearch, onLocation }: { ready: boolean; nearby: Stop[]; recent: ReturnType<typeof useRecentSelections>["items"]; onSearch: () => void; onLocation: () => void }) {
  return <section className={`roadmap-home-card ${ready ? "ready" : ""}`}>
    {ready ? <><button className="location-ready-row" type="button"><span><strong>Partindo da sua localização</strong>{nearby[0] && <small>Ponto mais próximo: {nearby[0].stop_name}</small>}</span><ChevronRight size={18} /></button><button className="roadmap-search-box compact" onClick={onSearch}><span>Para onde você quer ir?</span><Search size={18} /></button></> : <><h1>Para onde<br />você quer ir?</h1><button className="roadmap-search-box" onClick={onSearch}><span>Ex.: Savassi, Mineirão, Shopping Del Rey...</span><Search size={18} /></button><button className="roadmap-location-action" onClick={onLocation}><span><LocateFixed size={18} /></span><span><strong>Usar minha localização</strong><small>Para encontrar o ponto mais próximo</small></span><ChevronRight size={17} /></button></>}
    <div className="roadmap-section-title"><strong>Recentes</strong><Link href="/explorar">Ver todos</Link></div>
    <div className="roadmap-recent-list">{recent.slice(0, 3).map((item) => <button key={`${item.kind}-${item.id}`}><Clock3 size={16} /><span><strong>{item.label}</strong><small>{item.description}</small></span></button>)}{recent.length === 0 && ["Savassi", "Mineirão", "Shopping Del Rey"].map((label) => <button key={label} onClick={onSearch}><Clock3 size={16} /><span><strong>{label}</strong></span></button>)}</div>
  </section>;
}

function DestinationSearchScreen({ value, onChange, onCancel }: { value: string; onChange: (value: string) => void; onCancel: () => void }) {
  const shown = value.trim() ? developmentPlaces.filter((place) => place.toLowerCase().includes(value.toLowerCase()) || value.toLowerCase().includes("savassi")) : developmentPlaces;
  return <main className="roadmap-search-screen"><div className="search-top"><label><Search size={17} /><input autoFocus value={value} onChange={(event) => onChange(event.target.value)} placeholder="Para onde você quer ir?" />{value && <button onClick={() => onChange("")} aria-label="Limpar"><X size={16} /></button>}</label><button onClick={onCancel}>Cancelar</button></div><div className="search-tabs"><button className="active">Destinos</button><button>Lugares</button><button>Pontos</button><button>Linhas</button></div><div className="destination-results">{process.env.NODE_ENV !== "production" && <small className="preview-label">Preview de desenvolvimento: geocodificação pendente</small>}{shown.map((place, index) => <Link href="/rota?preview=1" key={place}><span><MapPin size={17} /></span><span><strong>{place}</strong><small>{index === 0 ? "Belo Horizonte - MG" : "Savassi, Belo Horizonte - MG"}</small></span><ChevronRight size={16} /></Link>)}</div><RoadmapNavigation active="home" /></main>;
}
