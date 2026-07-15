"use client";

import type { CSSProperties } from "react";
import { Home, MapPin, Menu, Route, Star } from "lucide-react";

export type MobileSection = "home" | "lines" | "stops" | "favorites" | "more";

type MobileBottomNavigationProps = {
  active: MobileSection;
  onSelect: (section: MobileSection) => void;
};

const items = [
  { id: "home", label: "Início", icon: Home },
  { id: "lines", label: "Linhas", icon: Route },
  { id: "stops", label: "Pontos", icon: MapPin },
  { id: "favorites", label: "Favoritos", icon: Star },
  { id: "more", label: "Mais", icon: Menu },
] as const;

export function MobileBottomNavigation({ active, onSelect }: MobileBottomNavigationProps) {
  const activeIndex = items.findIndex((item) => item.id === active);

  function selectSection(section: MobileSection) {
    if (section !== active) {
      navigator.vibrate?.(7);
    }
    onSelect(section);
  }

  return (
    <nav
      className="mobile-bottom-navigation floating-navigation"
      aria-label="Navegação principal"
      style={{ "--active-index": activeIndex } as CSSProperties}
    >
      <span className="floating-navigation-indicator" aria-hidden="true" />
      {items.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className={`floating-navigation-item${active === id ? " active" : ""}`}
          onClick={() => selectSection(id)}
          aria-current={active === id ? "page" : undefined}
        >
          <Icon size={20} strokeWidth={active === id ? 2.45 : 1.9} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
