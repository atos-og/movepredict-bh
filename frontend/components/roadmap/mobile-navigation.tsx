"use client";

import type { CSSProperties, MouseEvent } from "react";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Home, MapPin, Menu, Route, Star } from "lucide-react";

const items = [
  { id: "home", label: "Início", href: "/", icon: Home },
  { id: "lines", label: "Linhas", href: "/linhas", icon: Route },
  { id: "stops", label: "Pontos", href: "/pontos", icon: MapPin },
  { id: "favorites", label: "Favoritos", href: "/explorar?view=favorites", icon: Star },
  { id: "more", label: "Mais", href: "/explorar?view=more", icon: Menu },
] as const;

export function RoadmapNavigation({ active }: { active: (typeof items)[number]["id"] }) {
  const router = useRouter();
  const activeIndex = items.findIndex((item) => item.id === active);
  const [indicatorIndex, setIndicatorIndex] = useState(activeIndex);
  const navigationTimer = useRef<number | null>(null);

  useEffect(() => () => {
    if (navigationTimer.current) window.clearTimeout(navigationTimer.current);
  }, []);

  useEffect(() => {
    queueMicrotask(() => setIndicatorIndex(activeIndex));
  }, [activeIndex]);

  function navigate(event: MouseEvent<HTMLAnchorElement>, href: string, index: number) {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      index === activeIndex
    ) {
      return;
    }

    event.preventDefault();
    setIndicatorIndex(index);
    navigator.vibrate?.(7);
    if (navigationTimer.current) {
      window.clearTimeout(navigationTimer.current);
    }
    navigationTimer.current = window.setTimeout(() => {
      navigationTimer.current = null;
      router.push(href);
    }, 260);
  }

  return (
    <nav
      className="roadmap-nav floating-navigation"
      aria-label="Navegação principal"
      style={{ "--active-index": indicatorIndex } as CSSProperties}
    >
      <span className="floating-navigation-indicator" aria-hidden="true" />
      {items.map(({ id, label, href, icon: Icon }, index) => (
        <Link
          key={id}
          href={href}
          className={`floating-navigation-item${indicatorIndex === index ? " active" : ""}`}
          aria-current={active === id ? "page" : undefined}
          onClick={(event) => navigate(event, href, index)}
        >
          <Icon size={20} strokeWidth={indicatorIndex === index ? 2.45 : 1.9} />
          <span>{label}</span>
        </Link>
      ))}
    </nav>
  );
}
