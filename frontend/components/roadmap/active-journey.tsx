"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { BusFront, Layers3, LocateFixed } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { previewVehicle } from "@/lib/preview/roadmap-fixtures";

const RoadmapMap = dynamic(() => import("@/components/roadmap/roadmap-map").then((module) => module.RoadmapMap), { ssr: false });
const upcomingStops = ["Estação BH Bus", "Av. Amazonas", "Savassi", "Rua Sergipe", "Praça da Liberdade"];

export function ActiveJourney({ map = false, preview = false }: { map?: boolean; preview?: boolean }) {
  if (!preview) return <main className="roadmap-page"><AppHeader title="Viagem" backHref="/" /><section className="roadmap-unavailable"><BusFront size={30} /><h1>Nenhuma viagem em andamento</h1><p>Inicie uma rota real quando o planejador estiver conectado.</p></section></main>;
  if (map) return <main className="roadmap-page bus-map-page"><RoadmapMap userLocation={{ latitude: -19.931, longitude: -43.941 }} vehicles={[previewVehicle]} showVehicles /><div className="map-floating-actions"><button aria-label="Minha localização"><LocateFixed size={19} /></button><button aria-label="Camadas"><Layers3 size={19} /></button></div><section className="bus-map-card"><div><LineBadge value="1170" /><span><strong>Linha 1170</strong><small>Próximo ônibus em horário programado</small></span></div><BusFront size={22} /></section></main>;
  return <main className="roadmap-page active-route-page"><header className="active-line-header"><BusFront size={20} /><span><strong>Linha 1170</strong><small>Santa Lúcia / Mangabeiras</small></span></header><section className="next-stop"><small>Próxima parada</small><strong>Savassi</strong><span>09:28</span><p>Partida programada · em 4 paradas</p></section><ol className="upcoming-stops">{upcomingStops.map((stop, index) => <li className={stop === "Savassi" ? "selected" : ""} key={stop}><i /><span><strong>{stop}</strong><small>{`09:${String(5 + index * 7).padStart(2, "0")}`}</small></span></li>)}</ol><Link className="roadmap-primary route-bottom-action" href="/viagem?preview=1&map=1">Acompanhar no mapa</Link></main>;
}
