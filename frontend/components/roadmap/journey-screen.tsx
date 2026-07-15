"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BellRing, BusFront, ChevronRight, Footprints, LocateFixed, MapPin, RefreshCw, Route, Wifi, WifiOff } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { useGeolocation } from "@/hooks/use-geolocation";
import { journeyPlannerProvider } from "@/lib/adapters/journey-planner";
import { api } from "@/lib/api";
import { saveJourneyOffline, storeActiveJourney } from "@/lib/journey-storage";
import { previewJourney } from "@/lib/preview/roadmap-fixtures";
import type { GeocodedDestination, JourneyPlan, JourneyPreference, JourneyStep } from "@/types/mobility";
import type { VehiclePosition } from "@/types/realtime";

type PlanningState = "idle" | "loading" | "ready" | "empty" | "unavailable";

const preferenceLabels: Record<JourneyPreference, string> = {
  quickest: "Mais rapida",
  less_walking: "Menos caminhada",
  fewer_transfers: "Menos baldeacoes",
};

export function JourneyScreen({ details = false, preview = false, destination = null }: { details?: boolean; preview?: boolean; destination?: GeocodedDestination | null }) {
  const router = useRouter();
  const geo = useGeolocation();
  const [preference, setPreference] = useState<JourneyPreference>("quickest");
  const [plans, setPlans] = useState<JourneyPlan[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [state, setState] = useState<PlanningState>("idle");
  const [saved, setSaved] = useState(false);
  const [vehicles, setVehicles] = useState<VehiclePosition[]>([]);
  const [attempt, setAttempt] = useState(0);
  const selected = useMemo(() => plans.find((plan) => plan.id === selectedId) || plans[0] || null, [plans, selectedId]);

  useEffect(() => {
    if (preview || !destination || !geo.coordinates) return;
    let active = true;
    queueMicrotask(() => setState("loading"));
    void journeyPlannerProvider.plan(geo.coordinates, destination, preference).then((result) => {
      if (!active) return;
      if (result.status === "unavailable") { setPlans([]); setState("unavailable"); return; }
      setPlans(result.plans);
      setSelectedId(result.plans[0]?.id || null);
      setState(result.plans.length ? "ready" : "empty");
    });
    return () => { active = false; };
  }, [attempt, destination, geo.coordinates, preference, preview]);

  const selectedRouteId = selected?.lineIds[0];
  useEffect(() => {
    if (!selectedRouteId) { queueMicrotask(() => setVehicles([])); return; }
    let active = true;
    const refresh = () => void api.listVehicles(selectedRouteId).then((response) => {
      if (active) setVehicles(response.data);
    }).catch(() => { if (active) setVehicles([]); });
    refresh();
    const timer = window.setInterval(refresh, 20_000);
    return () => { active = false; window.clearInterval(timer); };
  }, [selectedRouteId]);

  if (preview) return details ? <RouteDetails plan={previewJourney} preview /> : <PreviewRoute />;
  if (!destination) return <Unavailable title="Escolha um destino" message="Volte ao inicio e informe para onde deseja ir." />;
  if (!geo.coordinates) return <LocationRequired destination={destination.label} geo={geo} />;
  if (state === "loading" || state === "idle") return <LoadingRoute destination={destination.label} />;
  if (state === "unavailable") return <Unavailable title="Planejador temporariamente indisponivel" message="A busca funcionou, mas o OpenTripPlanner nao respondeu. Sua localizacao e seu destino foram preservados." retry={() => setAttempt((value) => value + 1)} />;
  if (state === "empty") return <Unavailable title="Nenhuma rota encontrada" message="Nao encontramos uma combinacao de transporte publico para este destino neste horario." />;
  if (!selected) return null;

  const stored = { plan: selected, origin: geo.coordinates, destination, savedAt: new Date().toISOString() };
  function startJourney() {
    storeActiveJourney(stored);
    if ("Notification" in window && Notification.permission === "default") void Notification.requestPermission();
    router.push("/viagem");
  }

  if (details) return <RouteDetails plan={selected} onStart={startJourney} />;

  return <main className="roadmap-page journey-planner-page">
    <AppHeader title={destination.label} backHref="/" />
    <RoadmapMap userLocation={geo.coordinates} journeyGeometry={selected.geometry} vehicles={vehicles} showVehicles />
    <section className="journey-bottom-sheet" aria-live="polite">
      <div className="sheet-handle" aria-hidden="true" />
      <div className="journey-preferences" aria-label="Preferencia de rota">
        {(Object.keys(preferenceLabels) as JourneyPreference[]).map((value) => <button className={preference === value ? "active" : ""} key={value} onClick={() => setPreference(value)}>{preferenceLabels[value]}</button>)}
      </div>
      <header className="best-route-header"><span><small>Melhor opcao agora</small><strong>{selected.totalDurationMinutes} min</strong></span><RealtimeLabel plan={selected} /></header>
      <div className="route-mode-row"><Footprints size={16} /><span>{selected.walkingDurationMinutes} min a pe</span><BusFront size={16} /><strong>{selected.lineLabel}</strong><span>{selected.transferCount ? `${selected.transferCount} baldeacao(oes)` : "Direto"}</span></div>
      <p className="arrival-copy">{arrivalCopy(selected)}</p>
      {vehicles.length > 0 && <p className="vehicles-on-route"><BusFront size={14} />{vehicles.length} veiculo(s) desta linha no mapa agora.</p>}
      <button className="journey-details-link" onClick={() => router.push(`${window.location.pathname}${window.location.search}&details=1`)}>Ver trajeto passo a passo <ChevronRight size={17} /></button>
      {plans.length > 1 && <div className="journey-alternatives"><small>Outras opcoes</small>{plans.slice(1).map((plan) => <button key={plan.id} onClick={() => setSelectedId(plan.id)}><span><strong>{plan.totalDurationMinutes} min</strong><small>{plan.lineLabel}</small></span><ChevronRight size={16} /></button>)}</div>}
      <div className="journey-actions"><button className="roadmap-secondary" onClick={() => { saveJourneyOffline(stored); setSaved(true); }}><WifiOff size={17} />{saved ? "Salva no aparelho" : "Salvar offline"}</button><button className="roadmap-primary" onClick={startJourney}><Route size={18} />Iniciar viagem</button></div>
    </section>
  </main>;
}

function LocationRequired({ destination, geo }: { destination: string; geo: ReturnType<typeof useGeolocation> }) {
  return <main className="roadmap-page route-page"><AppHeader title={destination} backHref="/" /><section className="roadmap-unavailable"><LocateFixed size={30} /><h1>De onde voce esta saindo?</h1><p>Use sua localizacao para encontrarmos caminhada, ponto, linha e desembarque automaticamente.</p><button className="roadmap-primary" onClick={geo.requestLocation} disabled={geo.status === "requesting"}><LocateFixed size={18} />{geo.status === "requesting" ? "Obtendo localizacao..." : "Usar minha localizacao"}</button>{geo.status === "denied" && <p className="state-warning">Permissao negada. Libere a localizacao nas configuracoes do navegador.</p>}{["unavailable", "timeout", "unsupported"].includes(geo.status) && <p className="state-warning">Nao foi possivel obter a localizacao neste dispositivo. Tente novamente em uma conexao segura (HTTPS).</p>}</section></main>;
}

function LoadingRoute({ destination }: { destination: string }) {
  return <main className="roadmap-page route-page"><AppHeader title={destination} backHref="/" /><section className="roadmap-unavailable"><RefreshCw className="spin" size={30} /><h1>Montando sua melhor rota</h1><p>Combinando caminhada, linhas, horarios e previsoes disponiveis.</p></section></main>;
}

function Unavailable({ title, message, retry }: { title: string; message: string; retry?: () => void }) {
  return <main className="roadmap-page route-page"><AppHeader title="Planejar viagem" backHref="/" /><section className="roadmap-unavailable"><MapPin size={30} /><h1>{title}</h1><p>{message}</p>{retry && <button className="roadmap-primary" onClick={retry}><RefreshCw size={17} />Tentar novamente</button>}<Link className="roadmap-secondary" href="/">Voltar ao inicio</Link></section></main>;
}

function RealtimeLabel({ plan }: { plan: JourneyPlan }) {
  if (plan.realtimeStatus === "live") return <span className="realtime-pill live"><Wifi size={13} />Tempo real</span>;
  if (plan.realtimeStatus === "unavailable") return <span className="realtime-pill unavailable"><WifiOff size={13} />Sem previsao</span>;
  return <span className="realtime-pill scheduled">Horario programado</span>;
}

function arrivalCopy(plan: JourneyPlan): string {
  if (plan.nextBusArrival) return `Onibus previsto para ${formatTime(plan.nextBusArrival)}${plan.uncertaintySeconds ? `, variacao de ate ${Math.ceil(plan.uncertaintySeconds / 60)} min` : ""}.`;
  if (plan.scheduledDeparture) return `Partida programada para ${formatTime(plan.scheduledDeparture)}. A posicao do onibus ainda nao esta disponivel.`;
  return "A rota esta disponivel, mas nao ha previsao de chegada para este horario.";
}

function RouteDetails({ plan, preview = false, onStart }: { plan: JourneyPlan; preview?: boolean; onStart?: () => void }) {
  return <main className="roadmap-page route-details-page"><header className="route-summary-bar"><span><strong>{plan.totalDurationMinutes} min</strong><small>{plan.destinationLabel}</small></span><span>{plan.estimatedArrival ? `Chegada ${formatTime(plan.estimatedArrival)}` : "Chegada programada"}</span></header><JourneySteps plan={plan} /><button className="roadmap-primary route-bottom-action" onClick={onStart} disabled={preview && !onStart}><BellRing size={17} />{preview ? "Visualizacao da navegacao" : "Iniciar e avisar para descer"}</button></main>;
}

function JourneySteps({ plan, compact = false }: { plan: JourneyPlan; compact?: boolean }) {
  return <ol className={`roadmap-journey-steps ${compact ? "compact" : ""}`}>{plan.steps.map((step) => <JourneyStepRow key={step.id} step={step} />)}</ol>;
}

function JourneyStepRow({ step }: { step: JourneyStep }) {
  return <li><span>{step.kind === "bus" ? <BusFront size={16} /> : step.kind === "walk" ? <Footprints size={16} /> : <MapPin size={15} />}</span><div><strong>{step.title}</strong>{step.description && <small>{step.description}</small>}{step.kind === "bus" && <LineBadge value={step.routeShortName || step.routeId || "Onibus"} />}</div>{step.durationMinutes !== null && <small>{step.durationMinutes} min</small>}</li>;
}

function PreviewRoute() {
  return <main className="roadmap-page route-page"><section className="best-route"><header><span>Melhor opcao agora</span><small>Demonstracao programada</small><strong>32 min</strong></header><JourneySteps compact plan={previewJourney} /><div className="alternative-title">Outras opcoes</div>{[36, 41].map((minutes) => <button className="alternative-route" key={minutes}><strong>{minutes} min</strong><span><Footprints size={14} /> <BusFront size={14} /> programada</span><ChevronRight size={16} /></button>)}<Link className="roadmap-primary sticky-route-action" href="/rota?preview=1&details=1">Ver detalhes da rota</Link></section></main>;
}

function formatTime(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value.slice(0, 5) : parsed.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}
