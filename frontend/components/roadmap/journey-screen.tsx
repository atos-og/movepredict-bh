"use client";

import Link from "next/link";
import { BusFront, ChevronRight, Footprints, MapPin } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { previewJourney } from "@/lib/preview/roadmap-fixtures";

export function JourneyScreen({ details = false, preview = false }: { details?: boolean; preview?: boolean }) {
  if (!preview) return <main className="roadmap-page route-page"><AppHeader title="Planejar viagem" backHref="/" /><section className="roadmap-unavailable"><MapPin size={30} /><h1>Planejamento de viagem ainda não conectado</h1><p>Geocodificação e roteamento são necessários para calcular uma rota real. Nenhuma viagem foi simulada.</p><Link className="roadmap-primary" href="/">Voltar ao início</Link></section></main>;
  if (details) return <RouteDetails />;
  return <main className="roadmap-page route-page"><section className="best-route"><header><span>Melhor opção agora</span><small>Partida programada</small><strong>32 min</strong></header><JourneySteps compact /><div className="alternative-title">Outras opções</div>{[36, 41].map((minutes) => <button className="alternative-route" key={minutes}><strong>{minutes} min</strong><span><Footprints size={14} /> <BusFront size={14} /> programada</span><ChevronRight size={16} /></button>)}<Link className="roadmap-primary sticky-route-action" href="/rota?preview=1&details=1">Ver detalhes da rota</Link></section></main>;
}

function RouteDetails() {
  return <main className="roadmap-page route-details-page"><header className="route-summary-bar"><strong>32 min</strong><span>Chegada programada às 09:42</span></header><JourneySteps /><Link className="roadmap-primary route-bottom-action" href="/viagem?preview=1">Iniciar navegação</Link></main>;
}

function JourneySteps({ compact = false }: { compact?: boolean }) {
  return <ol className={`roadmap-journey-steps ${compact ? "compact" : ""}`}>{previewJourney.steps.map((step) => <li key={step.id}><span>{step.kind === "bus" ? <BusFront size={16} /> : step.kind === "walk" ? <Footprints size={16} /> : <MapPin size={15} />}</span><div><strong>{step.title}</strong>{step.description && <small>{step.description}</small>}{step.kind === "bus" && <LineBadge value="1170" />}</div>{step.durationMinutes && <small>{step.durationMinutes} min</small>}</li>)}</ol>;
}
