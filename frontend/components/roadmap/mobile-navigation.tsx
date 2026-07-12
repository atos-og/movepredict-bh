"use client";

import Link from "next/link";
import { Grid2X2, Home, MapPin, Menu, Star } from "lucide-react";

const items = [
  { id: "home", label: "Início", href: "/", icon: Home },
  { id: "lines", label: "Linhas", href: "/linhas", icon: Grid2X2 },
  { id: "stops", label: "Pontos", href: "/pontos", icon: MapPin },
  { id: "favorites", label: "Favoritos", href: "/?view=favorites", icon: Star },
  { id: "more", label: "Mais", href: "/explorar", icon: Menu },
] as const;

export function RoadmapNavigation({ active }: { active: (typeof items)[number]["id"] }) {
  return <nav className="roadmap-nav" aria-label="Navegação principal">{items.map(({ id, label, href, icon: Icon }) => <Link key={id} href={href} className={active === id ? "active" : ""} aria-current={active === id ? "page" : undefined}><Icon size={18} /><span>{label}</span></Link>)}</nav>;
}
