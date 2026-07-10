"use client";

import dynamic from "next/dynamic";
import {
  AlertCircle,
  ArrowLeft,
  BusFront,
  ChevronRight,
  Clock3,
  LocateFixed,
  MapPin,
  Menu,
  Route,
  Search,
  X,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Line, LineRoute, LineStop, PageMeta, Stop } from "@/types/transit";
import type { VehiclePosition } from "@/types/realtime";

const MapView = dynamic(() => import("@/components/map-view"), {
  ssr: false,
  loading: () => <div className="map-loading">Carregando mapa...</div>,
});

const PAGE_SIZE = 20;
const vehicles: VehiclePosition[] = [];

type SearchMode = "lines" | "stops";
type SidebarView = "results" | "itinerary";
type ApiStatus = "connecting" | "online" | "offline";
type DirectionId = "0" | "1";

export function TransitExplorer() {
  const [mode, setMode] = useState<SearchMode>("lines");
  const [sidebarView, setSidebarView] = useState<SidebarView>("results");
  const [query, setQuery] = useState("");
  const [lines, setLines] = useState<Line[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [lineMeta, setLineMeta] = useState<PageMeta | null>(null);
  const [stopMeta, setStopMeta] = useState<PageMeta | null>(null);
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showRoute, setShowRoute] = useState(true);
  const [showStops, setShowStops] = useState(true);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("connecting");
  const detailRequest = useRef(0);

  const runSearch = useCallback(async (searchMode: SearchMode, searchQuery: string) => {
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
      setError(caught instanceof ApiError ? caught.message : "Ocorreu um erro inesperado.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialSearch = window.setTimeout(() => void runSearch("lines", ""), 0);
    return () => window.clearTimeout(initialSearch);
  }, [runSearch]);

  function changeMode(nextMode: SearchMode) {
    detailRequest.current += 1;
    setMode(nextMode);
    setSidebarView("results");
    setQuery("");
    setError(null);
    setDetailError(null);
    setSelectedLine(null);
    setSelectedStop(null);
    setLineStops([]);
    setRoute(null);
    void runSearch(nextMode, "");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSidebarView("results");
    void runSearch(mode, query.trim());
  }

  async function loadMore() {
    setLoadingMore(true);
    setError(null);
    try {
      if (mode === "lines") {
        const response = await api.listLines(query.trim(), PAGE_SIZE, lines.length);
        setLines((current) => [...current, ...response.data]);
        setLineMeta(response.meta);
      } else {
        const response = await api.listStops(query.trim(), PAGE_SIZE, stops.length);
        setStops((current) => [...current, ...response.data]);
        setStopMeta(response.meta);
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Não foi possível carregar mais itens.");
    } finally {
      setLoadingMore(false);
    }
  }

  function selectLine(line: Line) {
    setSelectedLine(line);
    setSelectedStop(null);
    setSidebarView("itinerary");
    setSidebarOpen(false);
    setAvailableDirections([]);
    setDirectionsLoading(true);
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
    void loadLineDetails(line, undefined);
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
          setDirection(response.data.direction_id);
          setAvailableDirections((current) =>
            current.includes(response.data.direction_id as DirectionId)
              ? current
              : [...current, response.data.direction_id as DirectionId],
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

  function selectStop(stop: Stop) {
    detailRequest.current += 1;
    setSelectedStop(stop);
    setSelectedLine(null);
    setLineStops([]);
    setRoute(null);
    setSidebarOpen(false);
  }

  const results = mode === "lines" ? lines : stops;
  const meta = mode === "lines" ? lineMeta : stopMeta;
  const canLoadMore = Boolean(meta && results.length < meta.total);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true"><BusFront size={23} /></div>
          <div>
            <h1>MovePredict BH</h1>
            <p>Mobilidade em Belo Horizonte</p>
          </div>
        </div>
        <div className="topbar-status">
          <span className={`status-dot ${apiStatus}`} />
          <span>
            {apiStatus === "online"
              ? "Base GTFS conectada"
              : apiStatus === "offline"
                ? "API indisponível"
                : "Conectando à API"}
          </span>
          {apiStatus === "online" && <em>dados programados</em>}
        </div>
        <button
          className="icon-button mobile-menu"
          onClick={() => setSidebarOpen((current) => !current)}
          aria-label={sidebarOpen ? "Fechar busca" : "Abrir busca"}
          title={sidebarOpen ? "Fechar busca" : "Abrir busca"}
        >
          {sidebarOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </header>

      <section className="workspace">
        <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
          <div className="search-panel">
            <div className="segmented-control" aria-label="Tipo de busca">
              <button className={mode === "lines" ? "active" : ""} onClick={() => changeMode("lines")}>
                <Route size={17} /> Linhas
              </button>
              <button className={mode === "stops" ? "active" : ""} onClick={() => changeMode("stops")}>
                <MapPin size={17} /> Pontos
              </button>
            </div>

            <form className="search-form" onSubmit={submit}>
              <Search size={18} aria-hidden="true" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={mode === "lines" ? "Número ou destino da linha" : "Nome ou código do ponto"}
                aria-label={mode === "lines" ? "Buscar linha" : "Buscar ponto"}
              />
              <button type="submit" aria-label="Buscar" title="Buscar"><ChevronRight size={19} /></button>
            </form>
          </div>

          <div className="results-heading">
            {sidebarView === "itinerary" ? (
              <button className="back-to-results" onClick={() => setSidebarView("results")}>
                <ArrowLeft size={15} /> Voltar às linhas
              </button>
            ) : (
              <span>{query ? "Resultados" : mode === "lines" ? "Linhas disponíveis" : "Pontos disponíveis"}</span>
            )}
            {sidebarView === "results" && !loading && meta && (
              <strong>{results.length} de {meta.total}</strong>
            )}
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={18} />
              <span>{error}</span>
              <button onClick={() => void runSearch(mode, query)} aria-label="Tentar novamente">Tentar novamente</button>
            </div>
          )}

          {sidebarView === "itinerary" && selectedLine ? (
            <div className="itinerary-view">
              <div className="itinerary-line">
                <span className="line-badge" style={{ borderColor: safeColor(selectedLine.route_color) }}>
                  {selectedLine.route_short_name || selectedLine.route_id}
                </span>
                <div>
                  <strong>{selectedLine.route_long_name || "Itinerário sem nome"}</strong>
                  <small>
                    {route
                      ? `Trajeto ${route.shape_id}`
                      : routeLoading
                        ? "Carregando trajeto"
                        : "Trajeto indisponível"}
                  </small>
                </div>
              </div>
              <div className="direction-control" aria-label="Sentido da linha">
                <button
                  className={direction === "0" ? "active" : ""}
                  onClick={() => changeDirection("0")}
                  disabled={directionsLoading || !availableDirections.includes("0")}
                >
                  Ida
                </button>
                <button
                  className={direction === "1" ? "active" : ""}
                  onClick={() => changeDirection("1")}
                  disabled={directionsLoading || !availableDirections.includes("1")}
                >
                  Volta
                </button>
              </div>
              <div className="itinerary-title">
                <span>Pontos do trajeto</span>
                <strong>{stopsLoading ? "..." : lineStops.length}</strong>
              </div>
              {detailError && <div className="detail-error"><AlertCircle size={16} />{detailError}</div>}
              <div className="itinerary-stops" aria-busy={stopsLoading}>
                {stopsLoading ? (
                  <div className="itinerary-loading">
                    <span className="spinner" />
                    <strong>Buscando a sequência de pontos</strong>
                    <small>O arquivo GTFS de horários é grande; o trajeto aparece antes.</small>
                  </div>
                ) : (
                  lineStops.map((stop) => (
                    <button key={`${stop.stop_id}-${stop.stop_sequence}`} onClick={() => selectStop(stop)}>
                      <span>{stop.stop_sequence}</span>
                      <div><strong>{stop.stop_name}</strong><small>Código {stop.stop_code || stop.stop_id}</small></div>
                    </button>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="results-list" aria-busy={loading}>
              {loading ? (
                Array.from({ length: 5 }).map((_, index) => <div className="result-skeleton" key={index} />)
              ) : mode === "lines" ? (
                lines.map((line) => (
                  <button
                    className={`result-row ${selectedLine?.route_id === line.route_id ? "selected" : ""}`}
                    key={line.route_id}
                    onClick={() => selectLine(line)}
                  >
                    <span className="line-badge" style={{ borderColor: safeColor(line.route_color) }}>
                      {line.route_short_name || line.route_id}
                    </span>
                    <span className="result-copy">
                      <strong>{line.route_long_name || "Itinerário sem nome"}</strong>
                      <small>Linha {line.route_short_name || line.route_id}</small>
                    </span>
                    <ChevronRight size={17} />
                  </button>
                ))
              ) : (
                stops.map((stop) => (
                  <button
                    className={`result-row ${selectedStop?.stop_id === stop.stop_id ? "selected" : ""}`}
                    key={stop.stop_id}
                    onClick={() => selectStop(stop)}
                  >
                    <span className="stop-icon"><MapPin size={18} /></span>
                    <span className="result-copy">
                      <strong>{stop.stop_name}</strong>
                      <small>Ponto {stop.stop_code || stop.stop_id}</small>
                    </span>
                    <ChevronRight size={17} />
                  </button>
                ))
              )}
              {!loading && results.length === 0 && !error && (
                <div className="empty-state">
                  <Search size={25} />
                  <strong>Nenhum resultado</strong>
                  <span>Revise o termo e tente novamente.</span>
                </div>
              )}
              {!loading && canLoadMore && (
                <button className="load-more" onClick={() => void loadMore()} disabled={loadingMore}>
                  {loadingMore ? "Carregando..." : `Carregar mais ${mode === "lines" ? "linhas" : "pontos"}`}
                </button>
              )}
            </div>
          )}
        </aside>

        <div className="map-region">
          <MapView
            selectedStop={selectedStop}
            lineStops={lineStops}
            route={route}
            vehicles={vehicles}
            showRoute={showRoute}
            showStops={showStops}
            showVehicles={false}
          />

          <div className="map-toolbar" aria-label="Camadas do mapa">
            <label><input type="checkbox" checked={showRoute} onChange={(event) => setShowRoute(event.target.checked)} /><Route size={16} />Trajeto</label>
            <label><input type="checkbox" checked={showStops} onChange={(event) => setShowStops(event.target.checked)} /><MapPin size={16} />Pontos</label>
            <label className="unavailable" title="Aguardando integração dos dados em tempo real">
              <input type="checkbox" disabled /><BusFront size={16} />Veículos <em>em breve</em>
            </label>
          </div>

          {routeLoading && !route && (
            <div className="map-progress"><span className="spinner" />Carregando trajeto da linha...</div>
          )}

          {(selectedLine || selectedStop) && (
            <section className="selection-panel" aria-live="polite">
              <div className="selection-accent" />
              {selectedLine ? (
                <>
                  <div className="selection-main">
                    <span>Linha selecionada</span>
                    <strong>{selectedLine.route_short_name || selectedLine.route_id}</strong>
                    <p>{selectedLine.route_long_name || "Itinerário sem nome"}</p>
                  </div>
                  <div className="selection-stats">
                    <span><MapPin size={16} /><strong>{stopsLoading ? "..." : lineStops.length}</strong> pontos</span>
                    <span className="pending"><BusFront size={16} /><strong>--</strong> tempo real</span>
                    <span className="pending"><Clock3 size={16} /><strong>--</strong> previsões</span>
                  </div>
                </>
              ) : selectedStop ? (
                <>
                  <div className="selection-main">
                    <span>Ponto selecionado</span>
                    <strong>{selectedStop.stop_name}</strong>
                    <p>Código {selectedStop.stop_code || selectedStop.stop_id}</p>
                  </div>
                  <div className="selection-stats compact">
                    <span><LocateFixed size={16} />{selectedStop.stop_lat.toFixed(5)}, {selectedStop.stop_lon.toFixed(5)}</span>
                    <span className="pending"><Clock3 size={16} /><strong>--</strong> previsões</span>
                  </div>
                </>
              ) : null}
            </section>
          )}
        </div>
      </section>
    </main>
  );
}

function messageFrom(caught: unknown): string {
  return caught instanceof ApiError ? caught.message : "Não foi possível carregar os detalhes da linha.";
}

function safeColor(value: string | null): string {
  return value && /^[0-9a-f]{6}$/i.test(value) ? `#${value}` : "#07866f";
}
