"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  BusFront,
  ChevronRight,
  Clock3,
  Database,
  Info,
  MapPin,
  Route,
  ShieldCheck,
  Star,
} from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { useFavorites } from "@/hooks/use-favorites";
import { useRecentSelections } from "@/hooks/use-recent-selections";
import { selectionHref } from "@/lib/selections";
import type { RecentSelection } from "@/types/mobility";

type ExploreView = "recent" | "favorites" | "more";

export function ExploreSection() {
  const searchParams = useSearchParams();
  const requestedView = searchParams.get("view");
  const view: ExploreView = requestedView === "favorites" || requestedView === "more"
    ? requestedView
    : "recent";
  const favorites = useFavorites();
  const recent = useRecentSelections(20);
  const title = view === "favorites" ? "Favoritos" : view === "more" ? "Mais" : "Recentes";
  const active = view === "favorites" ? "favorites" : view === "more" ? "more" : "home";

  return (
    <main className="roadmap-page explore-page">
      <AppHeader title={title} backHref="/" />
      <section className="explore-content">
        {view === "recent" && <RecentView items={recent.items} />}
        {view === "favorites" && (
          <FavoritesView
            items={favorites.items}
            onRemove={(item) => favorites.toggle(item)}
          />
        )}
        {view === "more" && <MoreView />}
      </section>
      <RoadmapNavigation active={active} />
    </main>
  );
}

function RecentView({ items }: { items: RecentSelection[] }) {
  return (
    <>
      <header className="explore-heading">
        <h2>Vistos recentemente</h2>
        <p>Retome uma linha ou um ponto sem repetir a busca.</p>
      </header>
      {items.length ? <SelectionList items={items} /> : (
        <div className="roadmap-empty-state explore-empty">
          <Clock3 size={24} />
          <strong>Nenhuma consulta recente</strong>
          <span>As linhas e os pontos abertos aparecerao aqui.</span>
        </div>
      )}
      <nav className="explore-shortcuts" aria-label="Atalhos para explorar">
        <Link href="/linhas"><Route size={19} /><span><strong>Linhas</strong><small>Consulte trajetos oficiais</small></span><ChevronRight size={17} /></Link>
        <Link href="/pontos"><MapPin size={19} /><span><strong>Pontos</strong><small>Encontre paradas e previsoes</small></span><ChevronRight size={17} /></Link>
        <Link href="/explorar?view=favorites"><Star size={19} /><span><strong>Favoritos</strong><small>Acesse o que voce salvou</small></span><ChevronRight size={17} /></Link>
      </nav>
    </>
  );
}

function FavoritesView({ items, onRemove }: { items: RecentSelection[]; onRemove: (item: RecentSelection) => void }) {
  return (
    <>
      <header className="explore-heading">
        <h2>Seus favoritos</h2>
        <p>Linhas e pontos salvos para acesso rapido.</p>
      </header>
      {items.length ? <SelectionList items={items} onRemove={onRemove} /> : (
        <div className="roadmap-empty-state explore-empty">
          <Star size={24} />
          <strong>Nenhum favorito ainda</strong>
          <span>Use a estrela nos detalhes de uma linha ou de um ponto.</span>
        </div>
      )}
    </>
  );
}

function SelectionList({ items, onRemove }: { items: RecentSelection[]; onRemove?: (item: RecentSelection) => void }) {
  return (
    <div className="explore-selection-list">
      {items.map((item) => (
        <div className="explore-selection-row" key={`${item.kind}-${item.id}`}>
          <Link href={selectionHref(item)}>
            <span className="explore-selection-icon">{item.kind === "line" ? <BusFront size={18} /> : <MapPin size={18} />}</span>
            <span><strong>{item.label}</strong><small>{item.description}</small></span>
            {!onRemove && <ChevronRight size={17} />}
          </Link>
          {onRemove && (
            <button type="button" onClick={() => onRemove(item)} aria-label={`Remover ${item.label} dos favoritos`}>
              <Star size={18} fill="currentColor" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

function MoreView() {
  return (
    <>
      <header className="explore-heading">
        <h2>Sobre o MovePredict BH</h2>
        <p>Mobilidade inteligente feita para Belo Horizonte.</p>
      </header>
      <div className="about-list">
        <article><Database size={20} /><span><strong>Dados oficiais</strong><small>Linhas, pontos e trajetos programados da PBH (GTFS).</small></span></article>
        <article><BusFront size={20} /><span><strong>Tempo real</strong><small>Veiculos e previsoes aparecem quando a fonte esta disponivel.</small></span></article>
        <article><ShieldCheck size={20} /><span><strong>Privacidade</strong><small>Sua localizacao e usada apenas para planejar a viagem.</small></span></article>
        <article><Info size={20} /><span><strong>Versao de demonstracao</strong><small>Resultados dependem da disponibilidade dos servicos integrados.</small></span></article>
      </div>
    </>
  );
}
