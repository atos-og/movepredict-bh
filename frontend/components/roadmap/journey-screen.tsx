"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BusFront, ChevronRight, Footprints, LocateFixed, MapPin } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { useGeolocation } from "@/hooks/use-geolocation";
import { journeyPlannerProvider } from "@/lib/adapters/journey-planner";
import { previewJourney } from "@/lib/preview/roadmap-fixtures";
import type { GeocodedDestination, JourneyPlan } from "@/types/mobility";

export function JourneyScreen({ details = false, preview = false, destination = null }: { details?: boolean; preview?: boolean; destination?: GeocodedDestination | null }) {
  const geo = useGeolocation();
  const [plans, setPlans] = useState<JourneyPlan[]>([]);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "empty" | "unavailable">("idle");

  useEffect(() => {
    if (preview || !destination || !geo.coordinates) return;
    void journeyPlannerProvider.plan(geo.coordinates, destination).then((result) => {
      if (result.status === "unavailable") { setPlans([]); setState("unavailable"); return; }
      setPlans(result.plans);
      setState(result.plans.length ? "ready" : "empty");
    });
  }, [destination, geo.coordinates, preview]);

  if (preview) {
    if (details) return <RouteDetails />;
    return <PreviewRoute />;
  }

  if (!destination) return <Unavailable title="Escolha um destino" message="Volte ao inicio e informe para onde deseja ir." />;
  if (!geo.coordinates) return <main className="roadmap-page route-page"><AppHeader title={destination.label} backHref="/" /><section className="roadmap-unavailable"><LocateFixed size={30} /><h1>Precisamos da sua localizacao</h1><p>Ela e usada apenas para encontrar o ponto de partida e calcular a viagem.</p><button className="roadmap-primary" onClick={geo.requestLocation}><LocateFixed size={18} />Usar minha localizacao</button>{geo.status === "denied" && <p>Permissao negada. Libere a localizacao no navegador e tente novamente.</p>}{geo.status === "unavailable" && <p>Localizacao indisponivel neste dispositivo.</p>}</section></main>;
  if (state === "loading" || state === "idle") return <Unavailable title="Calculando sua viagem" message="Consultando caminhada, linhas e conexoes disponiveis." />;
  if (state === "unavailable") return <Unavailable title="Planejador temporariamente indisponivel" message="A busca de destino funcionou, mas o servidor OpenTripPlanner ainda nao esta configurado ou nao respondeu." />;
  if (state === "empty") return <Unavailable title="Nenhuma rota encontrada" message="Nao encontramos uma combinacao de transporte publico para este destino agora." />;

  return <main className="roadmap-page route-page"><AppHeader title={destination.label} backHref="/" /><section className="best-route">{plans.map((plan, index) => <article className="journey-result" key={plan.id}><header><span>{index === 0 ? "Melhor opcao agora" : "Alternativa"}</span><strong>{plan.totalDurationMinutes} min</strong></header><p><Footprints size={15} /> {plan.walkingDurationMinutes} min caminhando</p><p><BusFront size={15} /> Linha {plan.lineLabel} · {plan.transferCount} transferencia(s)</p><small>Sentido {plan.headsign}</small></article>)}</section></main>;
}

function Unavailable({ title, message }: { title: string; message: string }) {
  return <main className="roadmap-page route-page"><AppHeader title="Planejar viagem" backHref="/" /><section className="roadmap-unavailable"><MapPin size={30} /><h1>{title}</h1><p>{message}</p><Link className="roadmap-primary" href="/">Voltar ao inicio</Link></section></main>;
}

function PreviewRoute() {
  return <main className="roadmap-page route-page"><section className="best-route"><header><span>Melhor opcao agora</span><small>Partida programada</small><strong>32 min</strong></header><JourneySteps compact /><div className="alternative-title">Outras opcoes</div>{[36, 41].map((minutes) => <button className="alternative-route" key={minutes}><strong>{minutes} min</strong><span><Footprints size={14} /> <BusFront size={14} /> programada</span><ChevronRight size={16} /></button>)}<Link className="roadmap-primary sticky-route-action" href="/rota?preview=1&details=1">Ver detalhes da rota</Link></section></main>;
}

function RouteDetails() {
  return <main className="roadmap-page route-details-page"><header className="route-summary-bar"><strong>32 min</strong><span>Chegada programada as 09:42</span></header><JourneySteps /><Link className="roadmap-primary route-bottom-action" href="/viagem?preview=1">Iniciar navegacao</Link></main>;
}

function JourneySteps({ compact = false }: { compact?: boolean }) {
  return <ol className={`roadmap-journey-steps ${compact ? "compact" : ""}`}>{previewJourney.steps.map((step) => <li key={step.id}><span>{step.kind === "bus" ? <BusFront size={16} /> : step.kind === "walk" ? <Footprints size={16} /> : <MapPin size={15} />}</span><div><strong>{step.title}</strong>{step.description && <small>{step.description}</small>}{step.kind === "bus" && <LineBadge value="1170" />}</div>{step.durationMinutes && <small>{step.durationMinutes} min</small>}</li>)}</ol>;
}
