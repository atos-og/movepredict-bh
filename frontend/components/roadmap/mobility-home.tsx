"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ChevronRight, Clock3, LocateFixed, MapPin, Search, X } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LocationLoadingSheet } from "@/components/roadmap/location-loading-sheet";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useGeolocation } from "@/hooks/use-geolocation";
import { useRecentSelections } from "@/hooks/use-recent-selections";
import { geocodingProvider } from "@/lib/adapters/geocoding";
import { api } from "@/lib/api";
import { boundsAround, nearestStops } from "@/lib/geo";
import { readActiveJourney, readSavedJourneys, type StoredJourney } from "@/lib/journey-storage";
import type { Coordinates, GeocodedDestination } from "@/types/mobility";
import type { Stop } from "@/types/transit";

type HomeScreen = "home" | "permission" | "loading" | "ready" | "search";
const popularPlaces = ["Savassi", "Mineirao", "Shopping Del Rey", "Praca Sete"];

export function MobilityHome() {
  const params = useSearchParams();
  const requestedScreen = params.get("screen") as HomeScreen | null;
  const [screen, setScreen] = useState<HomeScreen>(requestedScreen || "home");
  const [query, setQuery] = useState("");
  const [nearby, setNearby] = useState<Stop[]>([]);
  const [activeJourney, setActiveJourney] = useState<StoredJourney | null>(null);
  const [savedJourney, setSavedJourney] = useState<StoredJourney | null>(null);
  const geolocation = useGeolocation();
  const recent = useRecentSelections();

  useEffect(() => {
    queueMicrotask(() => {
      setActiveJourney(readActiveJourney());
      setSavedJourney(readSavedJourneys()[0] || null);
    });
  }, []);

  useEffect(() => {
    if (!geolocation.coordinates) return;
    void api.listStopsInBounds(boundsAround(geolocation.coordinates, 1500), 60)
      .then((result) => setNearby(nearestStops(geolocation.coordinates!, result.data, 3)))
      .catch(() => setNearby([]));
  }, [geolocation.coordinates]);

  useEffect(() => {
    if (geolocation.status !== "granted") return;
    const timer = window.setTimeout(() => setScreen("ready"), 0);
    return () => window.clearTimeout(timer);
  }, [geolocation.status]);

  const previewCoordinates = requestedScreen === "ready" || requestedScreen === "loading"
    ? { latitude: -19.932, longitude: -43.938 }
    : null;
  const mapCoordinates = geolocation.coordinates || previewCoordinates;

  if (screen === "search") {
    return <DestinationSearchScreen
      value={query}
      origin={mapCoordinates}
      onChange={setQuery}
      onCancel={() => { setQuery(""); setScreen(mapCoordinates ? "ready" : "home"); }}
    />;
  }

  return <main className="roadmap-app">
    <AppHeader />
    <RoadmapMap userLocation={mapCoordinates} nearbyStops={nearby} />
    {screen === "permission" && <section className="roadmap-permission"><span><LocateFixed size={30} /></span><h1>Encontre a melhor rota saindo de onde voce esta</h1><p>Usaremos sua localizacao apenas para encontrar o ponto mais proximo e calcular sua viagem.</p><button className="roadmap-primary" onClick={() => { setScreen("loading"); geolocation.requestLocation(); }}><LocateFixed size={18} />Usar minha localizacao</button><button className="roadmap-text-button" onClick={() => setScreen("home")}>Agora nao</button></section>}
    {screen === "loading" && <><div className="location-pulse" aria-hidden="true"><i /></div><LocationLoadingSheet /></>}
    {(screen === "home" || screen === "ready") && <HomeCard ready={screen === "ready"} nearby={nearby} recent={recent.items} activeJourney={activeJourney} savedJourney={savedJourney} onSearch={() => setScreen("search")} onLocation={() => setScreen("permission")} />}
    {screen !== "loading" && <RoadmapNavigation active="home" />}
  </main>;
}

function HomeCard({ ready, nearby, recent, activeJourney, savedJourney, onSearch, onLocation }: { ready: boolean; nearby: Stop[]; recent: ReturnType<typeof useRecentSelections>["items"]; activeJourney: StoredJourney | null; savedJourney: StoredJourney | null; onSearch: () => void; onLocation: () => void }) {
  const resumable = activeJourney || savedJourney;
  return <section className={`roadmap-home-card ${ready ? "ready" : ""}`}>
    {ready ? <><button className="location-ready-row" type="button"><span><strong>Partindo da sua localizacao</strong>{nearby[0] && <small>Ponto mais proximo: {nearby[0].stop_name}</small>}</span><ChevronRight size={18} /></button><button className="roadmap-search-box compact" onClick={onSearch}><span>Para onde voce quer ir?</span><Search size={18} /></button></> : <><h1>Para onde<br />voce quer ir?</h1><button className="roadmap-search-box" onClick={onSearch}><span>Ex.: Savassi, Mineirao, Shopping Del Rey...</span><Search size={18} /></button><button className="roadmap-location-action" onClick={onLocation}><span><LocateFixed size={18} /></span><span><strong>Usar minha localizacao</strong><small>Para encontrar o ponto mais proximo</small></span><ChevronRight size={17} /></button></>}
    {resumable && <Link className="resume-journey" href={activeJourney ? "/viagem" : `/viagem?saved=${encodeURIComponent(resumable.plan.id)}`}><span><strong>{activeJourney ? "Retomar viagem" : "Abrir rota salva"}</strong><small>{resumable.destination.label}</small></span><ChevronRight size={17} /></Link>}
    <div className="roadmap-section-title"><strong>Recentes</strong><Link href="/explorar">Ver todos</Link></div>
    <div className="roadmap-recent-list">{recent.slice(0, 3).map((item) => <button key={`${item.kind}-${item.id}`}><Clock3 size={16} /><span><strong>{item.label}</strong><small>{item.description}</small></span></button>)}{recent.length === 0 && popularPlaces.slice(0, 3).map((label) => <button key={label} onClick={onSearch}><Clock3 size={16} /><span><strong>{label}</strong></span></button>)}</div>
  </section>;
}

function DestinationSearchScreen({ value, origin, onChange, onCancel }: { value: string; origin: Coordinates | null; onChange: (value: string) => void; onCancel: () => void }) {
  const [results, setResults] = useState<GeocodedDestination[]>([]);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "empty" | "unavailable">("idle");

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (value.trim().length < 2) return;
    setState("loading");
    const response = await geocodingProvider.search(value, origin || undefined);
    if (response.status === "unavailable") { setResults([]); setState("unavailable"); return; }
    setResults(response.data);
    setState(response.data.length ? "ready" : "empty");
  }

  function choosePopular(place: string) {
    onChange(place);
    setState("loading");
    void geocodingProvider.search(place, origin || undefined).then((response) => {
      if (response.status === "unavailable") { setResults([]); setState("unavailable"); return; }
      setResults(response.data);
      setState(response.data.length ? "ready" : "empty");
    });
  }

  return <main className="roadmap-search-screen">
    <form className="search-top" onSubmit={search}><label><Search size={17} /><input autoFocus value={value} onChange={(event) => { onChange(event.target.value); setState("idle"); setResults([]); }} placeholder="Para onde voce quer ir?" />{value && <button type="button" onClick={() => { onChange(""); setResults([]); setState("idle"); }} aria-label="Limpar"><X size={16} /></button>}</label><button type="submit" disabled={value.trim().length < 2 || state === "loading"}>Buscar</button><button type="button" onClick={onCancel} aria-label="Cancelar"><X size={18} /></button></form>
    <div className="search-tabs"><button className="active">Destinos</button><Link href="/pontos">Pontos</Link><Link href="/linhas">Linhas</Link></div>
    <div className="destination-results">
      {state === "loading" && <small className="preview-label">Buscando enderecos em Belo Horizonte...</small>}
      {state === "empty" && <small className="preview-label">Nenhum destino encontrado.</small>}
      {state === "unavailable" && <small className="preview-label">Busca de enderecos indisponivel. Tente novamente.</small>}
      {results.map((place) => <Link href={`/rota?destination=${encodeURIComponent(place.label)}&lat=${place.coordinates.latitude}&lon=${place.coordinates.longitude}`} key={place.id}><span><MapPin size={17} /></span><span><strong>{place.label}</strong><small>{place.description}</small></span><ChevronRight size={16} /></Link>)}
      {state === "idle" && popularPlaces.map((place) => <button type="button" key={place} onClick={() => choosePopular(place)}><span><MapPin size={17} /></span><span><strong>{place}</strong><small>Belo Horizonte - MG</small></span><ChevronRight size={16} /></button>)}
    </div>
    <small className="geocoding-attribution">Busca de enderecos por OpenStreetMap</small>
    <RoadmapNavigation active="home" />
  </main>;
}
