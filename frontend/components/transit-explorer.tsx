"use client";

import dynamic from "next/dynamic";
import {
  AlertCircle,
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
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Line, LineRoute, LineStop, Stop } from "@/types/transit";
import type { ArrivalPrediction, VehiclePosition } from "@/types/realtime";

const MapView = dynamic(() => import("@/components/map-view"), {
  ssr: false,
  loading: () => <div className="map-loading">Carregando mapa...</div>,
});

type SearchMode = "lines" | "stops";
type ApiStatus = "connecting" | "online" | "offline";

export function TransitExplorer() {
  const [mode, setMode] = useState<SearchMode>("lines");
  const [query, setQuery] = useState("");
  const [lines, setLines] = useState<Line[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [selectedLine, setSelectedLine] = useState<Line | null>(null);
  const [selectedStop, setSelectedStop] = useState<Stop | null>(null);
  const [lineStops, setLineStops] = useState<LineStop[]>([]);
  const [route, setRoute] = useState<LineRoute | null>(null);
  const [vehicles] = useState<VehiclePosition[]>([]);
  const [predictions] = useState<ArrivalPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showRoute, setShowRoute] = useState(true);
  const [showStops, setShowStops] = useState(true);
  const [showVehicles, setShowVehicles] = useState(true);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("connecting");

  const runSearch = useCallback(async (searchMode: SearchMode, searchQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      if (searchMode === "lines") {
        const response = await api.listLines(searchQuery);
        setLines(response.data);
      } else {
        const response = await api.listStops(searchQuery);
        setStops(response.data);
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
    setMode(nextMode);
    setQuery("");
    setError(null);
    void runSearch(nextMode, "");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(mode, query.trim());
  }

  async function selectLine(line: Line) {
    setSelectedLine(line);
    setSelectedStop(null);
    setDetailLoading(true);
    setError(null);
    setSidebarOpen(false);
    try {
      const [routeResult, stopsResult] = await Promise.allSettled([
        api.getLineRoute(line.route_id),
        api.getLineStops(line.route_id),
      ]);
      if (routeResult.status === "fulfilled") setRoute(routeResult.value.data);
      else setRoute(null);
      if (stopsResult.status === "fulfilled") setLineStops(stopsResult.value.data);
      else setLineStops([]);
      if (routeResult.status === "rejected" && stopsResult.status === "rejected") {
        throw routeResult.reason;
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Não foi possível abrir a linha.");
    } finally {
      setDetailLoading(false);
    }
  }

  function selectStop(stop: Stop) {
    setSelectedStop(stop);
    setSelectedLine(null);
    setLineStops([]);
    setRoute(null);
    setSidebarOpen(false);
  }

  const resultCount = mode === "lines" ? lines.length : stops.length;

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
              ? "GTFS conectado"
              : apiStatus === "offline"
                ? "API indisponível"
                : "Conectando à API"}
          </span>
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
            <span>{query ? "Resultados" : mode === "lines" ? "Linhas disponíveis" : "Pontos disponíveis"}</span>
            {!loading && <strong>{resultCount}</strong>}
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={18} />
              <span>{error}</span>
              <button onClick={() => void runSearch(mode, query)} aria-label="Tentar novamente">Tentar novamente</button>
            </div>
          )}

          <div className="results-list" aria-busy={loading}>
            {loading ? (
              Array.from({ length: 5 }).map((_, index) => <div className="result-skeleton" key={index} />)
            ) : mode === "lines" ? (
              lines.map((line) => (
                <button
                  className={`result-row ${selectedLine?.route_id === line.route_id ? "selected" : ""}`}
                  key={line.route_id}
                  onClick={() => void selectLine(line)}
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
            {!loading && resultCount === 0 && !error && (
              <div className="empty-state">
                <Search size={25} />
                <strong>Nenhum resultado</strong>
                <span>Revise o termo e tente novamente.</span>
              </div>
            )}
          </div>
        </aside>

        <div className="map-region">
          <MapView
            selectedStop={selectedStop}
            lineStops={lineStops}
            route={route}
            vehicles={vehicles}
            showRoute={showRoute}
            showStops={showStops}
            showVehicles={showVehicles}
          />

          <div className="map-toolbar" aria-label="Camadas do mapa">
            <label><input type="checkbox" checked={showRoute} onChange={(event) => setShowRoute(event.target.checked)} /><Route size={16} />Trajeto</label>
            <label><input type="checkbox" checked={showStops} onChange={(event) => setShowStops(event.target.checked)} /><MapPin size={16} />Pontos</label>
            <label><input type="checkbox" checked={showVehicles} onChange={(event) => setShowVehicles(event.target.checked)} /><BusFront size={16} />Veículos <span>{vehicles.length}</span></label>
          </div>

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
                    <span><MapPin size={16} /><strong>{detailLoading ? "..." : lineStops.length}</strong> pontos</span>
                    <span><BusFront size={16} /><strong>{vehicles.length}</strong> veículos</span>
                    <span><Clock3 size={16} /><strong>{predictions.length}</strong> previsões</span>
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
                    <span><Clock3 size={16} /><strong>{predictions.length}</strong> previsões</span>
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

function safeColor(value: string | null): string {
  return value && /^[0-9a-f]{6}$/i.test(value) ? `#${value}` : "#07866f";
}
