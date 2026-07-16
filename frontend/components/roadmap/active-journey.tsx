"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AlertTriangle, BellRing, BusFront, CheckCircle2, Footprints, Layers3, LocateFixed, MapPin, Navigation, RefreshCw, Signal, SignalZero } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapMap } from "@/components/roadmap/roadmap-map";
import { journeyPlannerProvider } from "@/lib/adapters/journey-planner";
import { api } from "@/lib/api";
import { distanceInMeters } from "@/lib/geo";
import { clearActiveJourney, readActiveJourney, readSavedJourney, storeActiveJourney, type StoredJourney } from "@/lib/journey-storage";
import { previewVehicle } from "@/lib/preview/roadmap-fixtures";
import type { Coordinates, JourneyPlan, JourneyStep, JourneyStop } from "@/types/mobility";
import type { ServiceAlert, VehiclePosition } from "@/types/realtime";

const OFF_ROUTE_METERS = 250;
const GET_OFF_ALERT_METERS = 600;

export function ActiveJourney({ map = false, preview = false, savedId = null }: { map?: boolean; preview?: boolean; savedId?: string | null }) {
  if (preview) return <PreviewJourney map={map} />;
  return <LiveJourney savedId={savedId} />;
}

function LiveJourney({ savedId }: { savedId: string | null }) {
  const [journey, setJourney] = useState<StoredJourney | null>(null);
  const [position, setPosition] = useState<Coordinates | null>(null);
  const [vehicles, setVehicles] = useState<VehiclePosition[]>([]);
  const [alerts, setAlerts] = useState<ServiceAlert[]>([]);
  const [online, setOnline] = useState(true);
  const [trackingError, setTrackingError] = useState<string | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const [alerted, setAlerted] = useState(false);
  const offRouteFixes = useRef(0);
  const lastRecalculation = useRef(0);

  useEffect(() => {
    queueMicrotask(() => {
      setJourney(savedId ? readSavedJourney(savedId) : readActiveJourney());
      setOnline(navigator.onLine);
    });
    const updateOnline = () => setOnline(navigator.onLine);
    window.addEventListener("online", updateOnline);
    window.addEventListener("offline", updateOnline);
    return () => { window.removeEventListener("online", updateOnline); window.removeEventListener("offline", updateOnline); };
  }, [savedId]);

  const recalculate = useCallback(async (origin: Coordinates, current: StoredJourney) => {
    if (!navigator.onLine || Date.now() - lastRecalculation.current < 120_000) return;
    lastRecalculation.current = Date.now();
    setRecalculating(true);
    const result = await journeyPlannerProvider.plan(origin, current.destination, current.plan.preference);
    if (result.status === "available" && result.plans[0]) {
      const updated = { ...current, origin, plan: result.plans[0], savedAt: new Date().toISOString() };
      storeActiveJourney(updated);
      setJourney(updated);
      offRouteFixes.current = 0;
    }
    setRecalculating(false);
  }, []);

  useEffect(() => {
    if (!journey || !("geolocation" in navigator)) return;
    const watch = navigator.geolocation.watchPosition((result) => {
      const next = { latitude: result.coords.latitude, longitude: result.coords.longitude };
      setPosition(next);
      setTrackingError(null);
      const distance = nearestDistance(next, journey.plan.geometry);
      offRouteFixes.current = distance > OFF_ROUTE_METERS ? offRouteFixes.current + 1 : 0;
      if (offRouteFixes.current >= 3) void recalculate(next, journey);
    }, (error) => {
      setTrackingError(error.code === error.PERMISSION_DENIED ? "Localizacao bloqueada. A rota offline continua disponivel." : "Sinal de localizacao indisponivel.");
    }, { enableHighAccuracy: true, maximumAge: 10_000, timeout: 20_000 });
    return () => navigator.geolocation.clearWatch(watch);
  }, [journey, recalculate]);

  const destinationStop = useMemo(() => findDestinationStop(journey?.plan || null), [journey]);
  useEffect(() => {
    if (!position || !destinationStop || alerted) return;
    if (distanceInMeters(position, destinationStop.coordinates) > GET_OFF_ALERT_METERS) return;
    queueMicrotask(() => setAlerted(true));
    navigator.vibrate?.([250, 150, 250]);
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("Hora de se preparar para descer", { body: `${destinationStop.name} esta proxima.`, icon: `${process.env.NEXT_PUBLIC_BASE_PATH || ""}/icon-192.png` });
    }
  }, [alerted, destinationStop, position]);

  const routeId = journey?.plan.lineIds[0];
  useEffect(() => {
    if (!routeId || !online) { queueMicrotask(() => setVehicles([])); return; }
    let active = true;
    const refresh = () => void api.listVehicles(routeId).then((response) => { if (active) setVehicles(response.data); }).catch(() => { if (active) setVehicles([]); });
    refresh();
    const timer = window.setInterval(refresh, 20_000);
    return () => { active = false; window.clearInterval(timer); };
  }, [online, routeId]);

  useEffect(() => {
    if (!online) return;
    let active = true;
    void api.listServiceAlerts().then((response) => {
      if (!active) return;
      setAlerts(response.data.filter((alert) => !routeId || !alert.route_ids.length || alert.route_ids.includes(routeId)));
    }).catch(() => { if (active) setAlerts([]); });
    return () => { active = false; };
  }, [online, routeId]);

  if (!journey) return <main className="roadmap-page"><AppHeader title="Viagem" backHref="/" /><section className="roadmap-unavailable"><BusFront size={30} /><h1>Nenhuma viagem em andamento</h1><p>Escolha um destino, confira a rota e toque em iniciar viagem.</p><Link className="roadmap-primary" href="/">Planejar uma viagem</Link></section></main>;

  const plan = journey.plan;
  const currentPosition = position || journey.origin;
  const progress = routeProgress(currentPosition, plan.geometry);
  const currentStep = stepAtProgress(plan, progress);
  const remainingStops = remainingStopCount(currentPosition, plan);

  return <main className="roadmap-page active-live-page">
    <RoadmapMap userLocation={currentPosition} journeyGeometry={plan.geometry} vehicles={vehicles} showVehicles />
    <div className="journey-live-status">{online ? <><Signal size={14} />Online</> : <><SignalZero size={14} />Rota offline</>}{recalculating && <><RefreshCw className="spin" size={14} />Recalculando</>}</div>
    <section className="active-journey-sheet">
      <div className="sheet-handle" aria-hidden="true" />
      {alerted && <div className="get-off-alert"><BellRing size={22} /><span><strong>Prepare-se para descer</strong><small>{destinationStop?.name}</small></span></div>}
      {alerts[0] && <div className="service-alert"><AlertTriangle size={20} /><span><strong>{alerts[0].title}</strong><small>{alerts[0].description || "Confira o impacto antes de continuar."}</small></span></div>}
      <header><span><small>Agora</small><strong>{currentStep.title}</strong><p>{currentStep.description || nextInstruction(currentStep)}</p></span><div className="journey-progress-ring">{Math.round(progress * 100)}%</div></header>
      <div className="active-route-facts"><span><MapPin size={16} /><strong>{remainingStops}</strong><small>paradas restantes</small></span><span><BusFront size={16} /><strong>{plan.lineLabel}</strong><small>{vehicles.length ? `${vehicles.length} veiculo(s) no mapa` : "sem veiculo visivel"}</small></span><span><Navigation size={16} /><strong>{Math.max(1, Math.round(plan.totalDurationMinutes * (1 - progress)))}</strong><small>min restantes</small></span></div>
      {trackingError && <p className="journey-inline-warning">{trackingError}</p>}
      <div className="active-next-steps">{nextSteps(plan, currentStep.id).map((step) => <div key={step.id}>{step.kind === "bus" ? <BusFront size={17} /> : step.kind === "walk" ? <Footprints size={17} /> : <MapPin size={17} />}<span><strong>{step.title}</strong><small>{step.description}</small></span></div>)}</div>
      <button className="finish-journey" onClick={() => { clearActiveJourney(); setJourney(null); }}><CheckCircle2 size={17} />Encerrar viagem</button>
    </section>
  </main>;
}

function nearestDistance(position: Coordinates, geometry: Coordinates[]): number {
  if (!geometry.length) return 0;
  return Math.min(...geometry.map((point) => distanceInMeters(position, point)));
}

function routeProgress(position: Coordinates, geometry: Coordinates[]): number {
  if (geometry.length < 2) return 0;
  let nearest = 0;
  let nearestMeters = Number.POSITIVE_INFINITY;
  geometry.forEach((point, index) => {
    const distance = distanceInMeters(position, point);
    if (distance < nearestMeters) { nearestMeters = distance; nearest = index; }
  });
  return nearest / (geometry.length - 1);
}

function stepAtProgress(plan: JourneyPlan, progress: number): JourneyStep {
  const weighted = plan.steps.filter((step) => step.durationMinutes !== null);
  if (!weighted.length) return plan.steps[0];
  const elapsed = progress * plan.totalDurationMinutes;
  let cursor = 0;
  for (const step of weighted) {
    cursor += step.durationMinutes || 0;
    if (elapsed <= cursor) return step;
  }
  return weighted[weighted.length - 1];
}

function findDestinationStop(plan: JourneyPlan | null): JourneyStop | null {
  if (!plan) return null;
  const transit = [...plan.steps].reverse().find((step) => step.kind === "bus");
  return transit?.toStop || null;
}

function remainingStopCount(position: Coordinates, plan: JourneyPlan): number {
  const transit = plan.steps.find((step) => step.kind === "bus");
  if (!transit) return 0;
  const stops = [...transit.intermediateStops, ...(transit.toStop ? [transit.toStop] : [])];
  if (!stops.length) return 0;
  let nearest = 0;
  let distance = Number.POSITIVE_INFINITY;
  stops.forEach((stop, index) => { const next = distanceInMeters(position, stop.coordinates); if (next < distance) { nearest = index; distance = next; } });
  return Math.max(0, stops.length - nearest);
}

function nextSteps(plan: JourneyPlan, currentId: string): JourneyStep[] {
  const index = plan.steps.findIndex((step) => step.id === currentId);
  return plan.steps.slice(Math.max(0, index + 1), index + 3);
}

function nextInstruction(step: JourneyStep): string {
  if (step.kind === "walk") return "Siga o trajeto indicado no mapa.";
  if (step.kind === "bus") return `Permaneca no onibus sentido ${step.headsign || "destino"}.`;
  return "Continue acompanhando a rota.";
}

function PreviewJourney({ map }: { map: boolean }) {
  if (map) return <main className="roadmap-page bus-map-page visual-preview"><RoadmapMap userLocation={{ latitude: -19.931, longitude: -43.941 }} vehicles={[previewVehicle]} showVehicles /><div className="map-floating-actions"><button aria-label="Minha localizacao"><LocateFixed size={19} /></button><button aria-label="Camadas"><Layers3 size={19} /></button></div><section className="bus-map-card"><div><LineBadge value="1170" /><span><strong>Linha 1170</strong><small>Proximo onibus em horario programado</small></span></div><BusFront size={22} /></section></main>;
  return <main className="roadmap-page active-route-page"><header className="active-line-header"><BusFront size={20} /><span><strong>Linha 1170</strong><small>Santa Lucia / Mangabeiras</small></span></header><section className="next-stop"><small>Proxima parada</small><strong>Savassi</strong><span>09:28</span><p>Partida programada - em 4 paradas</p></section><Link className="roadmap-primary route-bottom-action" href="/viagem?preview=1&map=1">Acompanhar no mapa</Link></main>;
}
