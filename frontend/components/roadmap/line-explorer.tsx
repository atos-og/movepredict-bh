"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight, RefreshCw, Search } from "lucide-react";
import { AppHeader } from "@/components/roadmap/app-header";
import { LineBadge } from "@/components/roadmap/line-badge";
import { RoadmapNavigation } from "@/components/roadmap/mobile-navigation";
import { api } from "@/lib/api";
import type { Line, PageMeta } from "@/types/transit";

export function LineExplorer() {
  const [lines, setLines] = useState<Line[]>([]);
  const [meta, setMeta] = useState<PageMeta | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async (offset = 0, append = false) => {
    setLoading(true); setError(false);
    try { const result = await api.listLines(query.trim(), 30, offset); setLines((current) => append ? [...current, ...result.data] : result.data); setMeta(result.meta); }
    catch { setError(true); }
    finally { setLoading(false); }
  }, [query]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timer); }, [load]);

  return <main className="roadmap-page list-page"><AppHeader title="Explorar linhas" backHref="/" /><section className="line-explorer-content"><label className="list-search"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar linha" /></label>{meta && <div className="list-count">{meta.total} linhas oficiais</div>}<div className="roadmap-line-list" aria-busy={loading}>{loading && lines.length === 0 ? Array.from({ length: 7 }).map((_, index) => <span className="roadmap-list-skeleton" key={index} />) : lines.map((line, index) => <Link href={`/linha/${encodeURIComponent(line.route_id)}`} key={line.route_id}><LineBadge value={line.route_short_name || line.route_id} tone={index % 4 === 0 ? "green" : index % 4 === 2 ? "orange" : "navy"} /><span><strong>{line.route_long_name || "Itinerário sem nome"}</strong><small>{line.route_short_name ? `Linha ${line.route_short_name}` : line.route_id}</small></span><ChevronRight size={16} /></Link>)}</div>{!loading && !error && meta?.total === 0 && <div className="roadmap-empty-state"><Search size={22} /><strong>Nenhuma linha encontrada</strong><span>Revise o termo e tente novamente.</span></div>}{error && <div className="roadmap-inline-error"><span>Não foi possível carregar as linhas.</span><button onClick={() => void load()}><RefreshCw size={15} />Tentar novamente</button></div>}{meta && lines.length < meta.total && <button className="roadmap-load-more" onClick={() => void load(lines.length, true)}>Ver mais linhas</button>}</section><RoadmapNavigation active="lines" /></main>;
}
