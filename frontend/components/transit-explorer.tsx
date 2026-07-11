"use client";

import dynamic from "next/dynamic";
import {
  AlertCircle,
  ArrowLeft,
  BusFront,
  ChevronRight,
  Clock3,
  Compass,
  LocateFixed,
  MapPin,
  Menu,
  Navigation,
  Route,
  Search,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { LocationStatus } from "@/components/location/location-status";
import { DestinationSearch } from "@/components/search/destination-search";
import { TransitSuggestions } from "@/components/search/transit-suggestions";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { Button } from "@/components/ui/button";
import { FeedbackState } from "@/components/ui/feedback-state";
import { SearchField } from "@/components/ui/search-field";
import { useGeolocation } from "@/hooks/use-geolocation";
import { useRecentSelections } from "@/hooks/use-recent-selections";
import { api, ApiError } from "@/lib/api";
import { boundsAround, distanceInMeters, formatDistance, nearestStops, stopCoordinates } from "@/lib/geo";
import type { RecentSelection } from "@/types/mobility";
import type { VehiclePosition } from "@/types/realtime";
import type { Line, LineRoute, LineStop, PageMeta, Stop } from "@/types/transit";

const MapView = dynamic(() => import("@/components/map-view"), {
  ssr: false,
  loading: () => <div className="map-loading">Carregando mapa...</div>,
});

const PAGE_SIZE = 20;
const SUGGESTION_LIMIT = 5;
const vehicles: VehiclePosition[] = [];

type SearchMode = "lines" | "stops";
type PanelView = "home" | "browse" | "line" | "stop";
type DetailOrigin = "home" | "browse" | "line";
type ApiStatus = "connecting" | "online" | "offline";
type DirectionId = "0" | "1";

export function TransitExplorer() {
  const [panelView, setPanelView] = useState<PanelView>("home");
  const [detailOrigin, setDetailOrigin] = useState<DetailOrigin>("home");
  const [panelOpen, setPanelOpen] = useState(true);
  const [mode, setMode] = useState<SearchMode>("lines");
  const [destinationQuery, setDestinationQuery] = useState("");
  const [browseQuery, setBrowseQuery] = useState("");
  const [lines, setLines] = useState<Line[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [lineMeta, setLineMeta] = useState<PageMeta | null>(null);
  const [stopMeta, setStopMeta] = useState<PageMeta | null>(null);
  const [suggestedLines, setSuggestedLines] = useState<Line[]>([]);
  const [suggestedStops, setSuggestedStops] = useState<Stop[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  const [selectedLine, setSelectedLine] = useState<Line | null>(null);
  const [selectedStop, setSelectedStop] = useState<Stop | null>(null);
  const [lineStops, setLineStops] = useState<LineStop[]>([]);
  const [route, setRoute] = useState<LineRoute | null>(null);
  const [direction, setDirection] = useState<DirectionId>("0");
  const [availableDirections, setAvailableDirections] = useState<DirectionId[]>([]);
  const [directionsLoading, setDirectionsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [routeLoading, setRouteLoading] = useState(false);
  const [stopsLoading, setStopsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [nearby, setNearby] = useState<Stop[]>([]);
  const [nearbyLoading, setNearbyLoading] = useState(false);
  const [nearbyError, setNearbyError] = useState(false);
  const [showRoute, setShowRoute] = useState(true);
  const [showStops, setShowStops] = useState(true);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("connecting");
  const [recenterToken, setRecenterToken] = useState(0);
  const detailRequest = useRef(0);
  const suggestionRequest = useRef(0);
  const geolocation = useGeolocation();
  const recentSelections = useRecentSelections();

  const runBrowse = useCallback(async (searchMode: SearchMode, searchQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      if (searchMode === "lines") {
        const response = await api.listLines(searchQuery, PAGE_SIZE);
        setLines(response.data);
        setLineMeta(response.meta);
      } else {
        const response = await api.listStops(searchQuery, PAGE_SIZE);
        setStops(response.data);
        setStopMeta(response.meta);
      }
      setApiStatus("online");
    } catch (caught) {
      setApiStatus("offline");
      setError(messageFrom(caught, "Não foi possível consultar a base oficial."));
    } finally {
      setLoading(false);
    }
  }, []);

  const runUnifiedSearch = useCallback(async (query: string) => {
    const normalized = query.trim();
    if (normalized.length < 2) return;
    const requestId = ++suggestionRequest.current;
    setSuggestionsLoading(true);
    setSuggestionError(null);

    const [lineResult, stopResult] = await Promise.allSettled([
      api.listLines(normalized, SUGGESTION_LIMIT),
      api.listStops(normalized, SUGGESTION_LIMIT),
    ]);
    if (suggestionRequest.current !== requestId) return;

    const nextLines = lineResult.status === "fulfilled" ? lineResult.value.data : [];
    const nextStops = stopResult.status === "fulfilled" ? stopResult.value.data : [];
    setSuggestedLines(nextLines);
    setSuggestedStops(nextStops);
    setSuggestionsLoading(false);

    if (lineResult.status === "rejected" && stopResult.status === "rejected") {
      setApiStatus("offline");
      setSuggestionError("Não foi possível consultar linhas e pontos agora.");
    } else {
      setApiStatus("online");
    }
  }, []);

  useEffect(() => {
    const initialSearch = window.setTimeout(() => void runBrowse("lines", ""), 0);
    return () => window.clearTimeout(initialSearch);
  }, [runBrowse]);

  useEffect(() => {
    const normalized = destinationQuery.trim();
    if (normalized.length < 2) return;
    const debounce = window.setTimeout(() => void runUnifiedSearch(normalized), 280);
    return () => window.clearTimeout(debounce);
  }, [destinationQuery, runUnifiedSearch]);

  useEffect(() => {
    if (!geolocation.coordinates) {
      const clearNearby = window.setTimeout(() => setNearby([]), 0);
      return () => window.clearTimeout(clearNearby);
    }
    let active = true;
    const coordinates = geolocation.coordinates;
    const nearbyRequest = window.setTimeout(() => {
      setNearbyLoading(true);
      setNearbyError(false);
      void api
        .listStopsInBounds(boundsAround(coordinates, 1_500))
        .then((response) => {
          if (active) setNearby(nearestStops(coordinates, response.data, 3));
        })
        .catch(() => {
          if (active) setNearbyError(true);
        })
        .finally(() => {
          if (active) setNearbyLoading(false);
        });
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(nearbyRequest);
    };
  }, [geolocation.coordinates]);

  function openHome() {
    detailRequest.current += 1;
    setPanelView("home");
    setSelectedLine(null);
    setSelectedStop(null);
    setLineStops([]);
    setRoute(null);
    setDetailError(null);
    setPanelOpen(true);
  }

  function resetHome() {
    changeDestinationQuery("");
    openHome();
  }

  function openBrowse(nextMode: SearchMode) {
    detailRequest.current += 1;
    setMode(nextMode);
    setPanelView("browse");
    setBrowseQuery("");
    setSelectedLine(null);
    setSelectedStop(null);
    setLineStops([]);
    setRoute(null);
    setDetailError(null);
    setPanelOpen(true);
    void runBrowse(nextMode, "");
  }

  function changeMode(nextMode: SearchMode) {
    if (nextMode === mode && panelView === "browse") return;
    openBrowse(nextMode);
  }

  function submitBrowse() {
    void runBrowse(mode, browseQuery.trim());
  }

  function submitDestination() {
    const normalized = destinationQuery.trim();
    if (normalized.length >= 2) void runUnifiedSearch(normalized);
  }

  function changeDestinationQuery(value: string) {
    setDestinationQuery(value);
    if (value.trim().length >= 2) {
      setSuggestionsLoading(true);
      setSuggestionError(null);
    } else {
      suggestionRequest.current += 1;
      setSuggestedLines([]);
      setSuggestedStops([]);
      setSuggestionsLoading(false);
      setSuggestionError(null);
    }
  }

  async function loadMore() {
    setLoadingMore(true);
    setError(null);
    try {
      if (mode === "lines") {
        const response = await api.listLines(browseQuery.trim(), PAGE_SIZE, lines.length);
        setLines((current) => [...current, ...response.data]);
        setLineMeta(response.meta);
      } else {
        const response = await api.listStops(browseQuery.trim(), PAGE_SIZE, stops.length);
        setStops((current) => [...current, ...response.data]);
        setStopMeta(response.meta);
      }
    } catch (caught) {
      setError(messageFrom(caught, "Não foi possível carregar mais itens."));
    } finally {
      setLoadingMore(false);
    }
  }

  function selectLine(line: Line, origin: DetailOrigin = "home") {
    setDetailOrigin(origin);
    setSelectedLine(line);
    setSelectedStop(null);
    setPanelView("line");
    setPanelOpen(true);
    setAvailableDirections([]);
    setDirectionsLoading(true);
    recentSelections.remember(toRecentLine(line));
    void api
      .listLineTrips(line.route_id)
      .then((response) => {
        const directions = Array.from(
          new Set(
            response.data
              .map((trip) => trip.direction_id)
              .filter((value): value is DirectionId => value === "0" || value === "1"),
          ),
        );
        setAvailableDirections(directions);
      })
      .catch(() => setAvailableDirections([]))
      .finally(() => setDirectionsLoading(false));
    void loadLineDetails(line);
  }

  async function loadLineDetails(line: Line, requestedDirection?: DirectionId) {
    const requestId = ++detailRequest.current;
    setRoute(null);
    setLineStops([]);
    setRouteLoading(true);
    setStopsLoading(true);
    setDetailError(null);

    const routeRequest = api
      .getLineRoute(line.route_id, requestedDirection)
      .then((response) => {
        if (detailRequest.current !== requestId) return;
        setRoute(response.data);
        if (response.data.direction_id === "0" || response.data.direction_id === "1") {
          const responseDirection = response.data.direction_id;
          setDirection(responseDirection);
          setAvailableDirections((current) =>
            current.includes(responseDirection) ? current : [...current, responseDirection],
          );
        }
      })
      .catch((caught) => {
        if (detailRequest.current === requestId) setDetailError(messageFrom(caught));
      })
      .finally(() => {
        if (detailRequest.current === requestId) setRouteLoading(false);
      });

    const stopsRequest = api
      .getLineStops(line.route_id, requestedDirection)
      .then((response) => {
        if (detailRequest.current === requestId) setLineStops(response.data);
      })
      .catch((caught) => {
        if (detailRequest.current === requestId) setDetailError(messageFrom(caught));
      })
      .finally(() => {
        if (detailRequest.current === requestId) setStopsLoading(false);
      });

    await Promise.allSettled([routeRequest, stopsRequest]);
  }

  function changeDirection(nextDirection: DirectionId) {
    if (!selectedLine || nextDirection === direction) return;
    setDirection(nextDirection);
    void loadLineDetails(selectedLine, nextDirection);
  }

  function selectStop(stop: Stop, origin: DetailOrigin = "home") {
    detailRequest.current += 1;
    setDetailOrigin(origin);
    setSelectedStop(stop);
    if (origin !== "line") {
      setSelectedLine(null);
      setLineStops([]);
      setRoute(null);
    }
    setPanelView("stop");
    setPanelOpen(true);
    recentSelections.remember(toRecentStop(stop));
  }

  function selectRecent(selection: RecentSelection) {
    if (selection.kind === "line") selectLine(selection.value, "home");
    else selectStop(selection.value, "home");
  }

  function backFromDetail() {
    if (panelView === "stop" && detailOrigin === "line" && selectedLine) {
      setSelectedStop(null);
      setPanelView("line");
      return;
    }
    if (detailOrigin === "browse") {
      setSelectedLine(null);
      setSelectedStop(null);
      setRoute(null);
      setLineStops([]);
      setPanelView("browse");
    } else {
      openHome();
    }
  }

  const results = mode === "lines" ? lines : stops;
  const meta = mode === "lines" ? lineMeta : stopMeta;
  const canLoadMore = Boolean(meta && results.length < meta.total);
  const hasDestinationQuery = destinationQuery.trim().length >= 2;
  const location = geolocation.coordinates;

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="brand-block" onClick={resetHome} aria-label="Ir para o início">
          <span className="brand-mark" aria-hidden="true"><BusFront size={23} /></span>
          <span><strong>MovePredict BH</strong><small>Mobilidade em Belo Horizonte</small></span>
        </button>
        <div className="topbar-status">
          <span className={`status-dot ${apiStatus}`} />
          <span>{apiStatus === "online" ? "Base oficial conectada" : apiStatus === "offline" ? "API indisponível" : "Conectando"}</span>
          {apiStatus === "online" && <em>GTFS programado</em>}
        </div>
        <Button
          className="icon-button mobile-menu"
          variant="icon"
          onClick={() => setPanelOpen((current) => !current)}
          aria-label={panelOpen ? "Recolher painel" : "Abrir painel"}
          title={panelOpen ? "Recolher painel" : "Abrir painel"}
        >
          {panelOpen ? <X size={21} /> : <Menu size={21} />}
        </Button>
      </header>

      <section className="workspace">
        <div className="map-region">
          <MapView
            selectedStop={selectedStop}
            lineStops={lineStops}
            route={route}
            userLocation={location}
            nearbyStops={nearby}
            vehicles={vehicles}
            showRoute={showRoute}
            showStops={showStops}
            showVehicles={false}
            recenterToken={recenterToken}
            onStopSelect={(stop) => selectStop(stop, "home")}
          />

          <div className="map-actions">
            {location && (
              <Button variant="icon" onClick={() => setRecenterToken((value) => value + 1)} aria-label="Centralizar na minha localização" title="Minha localização">
                <Navigation size={18} />
              </Button>
            )}
            <div className="map-toolbar" aria-label="Camadas do mapa">
              <label title="Mostrar trajeto"><input type="checkbox" checked={showRoute} onChange={(event) => setShowRoute(event.target.checked)} /><Route size={16} /><span>Trajeto</span></label>
              <label title="Mostrar pontos"><input type="checkbox" checked={showStops} onChange={(event) => setShowStops(event.target.checked)} /><MapPin size={16} /><span>Pontos</span></label>
            </div>
          </div>

          {routeLoading && !route && <div className="map-progress"><span className="spinner" />Carregando trajeto...</div>}
        </div>

        <BottomSheet
          className={`experience-panel view-${panelView} ${panelView === "home" && hasDestinationQuery ? "has-query" : ""}`}
          open={panelOpen}
        >
          {panelView === "home" && (
            <div className="home-view">
              <div className="home-search-block">
                <DestinationSearch
                  value={destinationQuery}
                  onChange={changeDestinationQuery}
                  onSubmit={submitDestination}
                  onClear={() => changeDestinationQuery("")}
                />
              </div>

              {hasDestinationQuery ? (
                <div className="home-scroll">
                  <TransitSuggestions
                    query={destinationQuery.trim()}
                    lines={suggestedLines}
                    stops={suggestedStops}
                    loading={suggestionsLoading}
                    error={suggestionError}
                    onLineSelect={(line) => selectLine(line, "home")}
                    onStopSelect={(stop) => selectStop(stop, "home")}
                  />
                </div>
              ) : (
                <div className="home-scroll home-content">
                  <LocationStatus status={geolocation.status} onRetry={geolocation.requestLocation} />

                  {geolocation.status === "granted" && (
                    <section className="nearby-section">
                      <div className="section-heading"><span>Perto de você</span>{nearbyLoading && <span className="spinner" />}</div>
                      {!nearbyLoading && nearbyError && <p className="inline-note">Não foi possível consultar pontos próximos.</p>}
                      {!nearbyLoading && !nearbyError && nearby.length === 0 && <p className="inline-note">Nenhum ponto encontrado em um raio de 1,5 km.</p>}
                      {nearby.map((stop) => (
                        <button key={stop.stop_id} className="nearby-row" onClick={() => selectStop(stop, "home")}>
                          <span className="stop-icon"><MapPin size={17} /></span>
                          <span><strong>{stop.stop_name}</strong><small>{location ? `${formatDistance(distanceInMeters(location, stopCoordinates(stop)))} em linha reta` : "Ponto próximo"}</small></span>
                          <ChevronRight size={17} />
                        </button>
                      ))}
                    </section>
                  )}

                  <section className="explore-section">
                    <div className="section-heading"><span>Explorar a rede</span></div>
                    <div className="explore-actions">
                      <Button variant="secondary" onClick={() => openBrowse("lines")}><Route size={18} />Linhas</Button>
                      <Button variant="secondary" onClick={() => openBrowse("stops")}><MapPin size={18} />Pontos</Button>
                    </div>
                  </section>

                  {recentSelections.items.length > 0 && (
                    <section className="recent-section">
                      <div className="section-heading"><span>Buscas recentes</span></div>
                      {recentSelections.items.map((selection) => (
                        <button key={`${selection.kind}-${selection.id}`} className="recent-row" onClick={() => selectRecent(selection)}>
                          {selection.kind === "line" ? <Route size={17} /> : <MapPin size={17} />}
                          <span><strong>{selection.label}</strong><small>{selection.description}</small></span>
                          <ChevronRight size={16} />
                        </button>
                      ))}
                    </section>
                  )}
                </div>
              )}
            </div>
          )}

          {panelView === "browse" && (
            <div className="browse-view">
              <PanelHeader title="Explorar transporte" onBack={openHome} />
              <div className="browse-search">
                <div className="segmented-control" aria-label="Tipo de busca">
                  <button className={mode === "lines" ? "active" : ""} onClick={() => changeMode("lines")}><Route size={17} />Linhas</button>
                  <button className={mode === "stops" ? "active" : ""} onClick={() => changeMode("stops")}><MapPin size={17} />Pontos</button>
                </div>
                <SearchField
                  value={browseQuery}
                  onChange={setBrowseQuery}
                  onSubmit={submitBrowse}
                  placeholder={mode === "lines" ? "Número ou nome da linha" : "Nome ou código do ponto"}
                  label={mode === "lines" ? "Buscar linha" : "Buscar ponto"}
                />
              </div>
              <div className="results-heading"><span>{browseQuery ? "Resultados" : mode === "lines" ? "Todas as linhas" : "Todos os pontos"}</span>{!loading && meta && <strong>{results.length} de {meta.total}</strong>}</div>
              {error && <div className="error-banner" role="alert"><AlertCircle size={18} /><span>{error}</span><Button variant="ghost" size="sm" onClick={submitBrowse}>Tentar novamente</Button></div>}
              <div className="results-list" aria-busy={loading}>
                {loading ? Array.from({ length: 5 }).map((_, index) => <div className="result-skeleton" key={index} />) : mode === "lines" ? (
                  lines.map((line) => <LineResult key={line.route_id} line={line} onSelect={() => selectLine(line, "browse")} />)
                ) : (
                  stops.map((stop) => <StopResult key={stop.stop_id} stop={stop} onSelect={() => selectStop(stop, "browse")} />)
                )}
                {!loading && results.length === 0 && !error && <FeedbackState icon={<Search size={24} />} title="Nenhum resultado" description="Revise o termo e tente novamente." />}
                {!loading && canLoadMore && <Button className="load-more" variant="secondary" onClick={() => void loadMore()} disabled={loadingMore}>{loadingMore ? "Carregando..." : `Carregar mais ${mode === "lines" ? "linhas" : "pontos"}`}</Button>}
              </div>
            </div>
          )}

          {panelView === "line" && selectedLine && (
            <div className="line-view">
              <PanelHeader title="Detalhes da linha" onBack={backFromDetail} />
              <div className="line-summary">
                <span className="line-badge large" style={{ borderColor: safeColor(selectedLine.route_color) }}>{selectedLine.route_short_name || selectedLine.route_id}</span>
                <span><strong>{selectedLine.route_long_name || "Itinerário sem nome"}</strong><small>{route ? "Trajeto oficial carregado" : routeLoading ? "Carregando trajeto" : "Trajeto indisponível"}</small></span>
              </div>
              <div className="direction-control" aria-label="Sentido da linha">
                <button className={direction === "0" ? "active" : ""} onClick={() => changeDirection("0")} disabled={directionsLoading || !availableDirections.includes("0")}>Ida</button>
                <button className={direction === "1" ? "active" : ""} onClick={() => changeDirection("1")} disabled={directionsLoading || !availableDirections.includes("1")}>Volta</button>
              </div>
              <div className="detail-capability"><Clock3 size={16} /><span><strong>Horários em tempo real ainda não disponíveis</strong><small>O mapa exibe o trajeto e os pontos do GTFS programado.</small></span></div>
              <div className="itinerary-title"><span>Pontos do trajeto</span><strong>{stopsLoading ? "..." : lineStops.length}</strong></div>
              {detailError && <div className="detail-error"><AlertCircle size={16} />{detailError}</div>}
              <div className="itinerary-stops" aria-busy={stopsLoading}>
                {stopsLoading ? <div className="itinerary-loading"><span className="spinner" /><strong>Buscando a sequência de pontos</strong><small>O trajeto aparece primeiro enquanto a base de horários é consultada.</small></div> : lineStops.map((stop) => (
                  <button key={`${stop.stop_id}-${stop.stop_sequence}`} onClick={() => selectStop(stop, "line")}><span>{stop.stop_sequence}</span><div><strong>{stop.stop_name}</strong><small>Código {stop.stop_code || stop.stop_id}</small></div></button>
                ))}
              </div>
            </div>
          )}

          {panelView === "stop" && selectedStop && (
            <div className="stop-view">
              <PanelHeader title="Detalhes do ponto" onBack={backFromDetail} />
              <div className="stop-summary"><span className="stop-icon large"><MapPin size={22} /></span><span><strong>{selectedStop.stop_name}</strong><small>Ponto {selectedStop.stop_code || selectedStop.stop_id}</small></span></div>
              {location && (
                <div className="distance-summary"><LocateFixed size={18} /><span><strong>{formatDistance(distanceInMeters(location, stopCoordinates(selectedStop)))}</strong><small>distância em linha reta da sua localização</small></span></div>
              )}
              <div className="stop-coordinates"><Compass size={17} /><span>{selectedStop.stop_lat.toFixed(5)}, {selectedStop.stop_lon.toFixed(5)}</span></div>
              <section className="integration-placeholder">
                <BusFront size={20} />
                <div><strong>Chegadas e linhas deste ponto</strong><p>A API atual ainda não relaciona um ponto às linhas que o atendem nem fornece previsões. Esta área está pronta para receber esses dados sem simulação.</p></div>
              </section>
              <section className="integration-placeholder">
                <Navigation size={20} />
                <div><strong>Rota até este ponto</strong><p>Tempo e caminho a pé dependem de um serviço de roteamento. A distância acima é apenas geográfica e está identificada como tal.</p></div>
              </section>
            </div>
          )}
        </BottomSheet>
      </section>
    </main>
  );
}

function PanelHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return <header className="panel-header"><Button variant="ghost" size="sm" onClick={onBack} aria-label="Voltar"><ArrowLeft size={18} /></Button><strong>{title}</strong><span /></header>;
}

function LineResult({ line, onSelect }: { line: Line; onSelect: () => void }) {
  return <button className="result-row" onClick={onSelect}><span className="line-badge" style={{ borderColor: safeColor(line.route_color) }}>{line.route_short_name || line.route_id}</span><span className="result-copy"><strong>{line.route_long_name || "Itinerário sem nome"}</strong><small>Linha {line.route_short_name || line.route_id}</small></span><ChevronRight size={17} /></button>;
}

function StopResult({ stop, onSelect }: { stop: Stop; onSelect: () => void }) {
  return <button className="result-row" onClick={onSelect}><span className="stop-icon"><MapPin size={18} /></span><span className="result-copy"><strong>{stop.stop_name}</strong><small>Ponto {stop.stop_code || stop.stop_id}</small></span><ChevronRight size={17} /></button>;
}

function toRecentLine(line: Line): RecentSelection {
  return { kind: "line", id: line.route_id, label: `Linha ${line.route_short_name || line.route_id}`, description: line.route_long_name || "Itinerário sem nome", value: line };
}

function toRecentStop(stop: Stop): RecentSelection {
  return { kind: "stop", id: stop.stop_id, label: stop.stop_name, description: `Ponto ${stop.stop_code || stop.stop_id}`, value: stop };
}

function messageFrom(caught: unknown, fallback = "Não foi possível carregar os detalhes da linha."): string {
  return caught instanceof ApiError ? caught.message : fallback;
}

function safeColor(value: string | null): string {
  return value && /^[0-9a-f]{6}$/i.test(value) ? `#${value}` : "#087c69";
}
