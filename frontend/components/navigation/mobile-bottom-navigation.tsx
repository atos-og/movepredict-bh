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
  return (
    <nav className="mobile-bottom-navigation" aria-label="Navegação principal">
      {items.map(({ id, label, icon: Icon }) => (
        <button key={id} className={active === id ? "active" : ""} onClick={() => onSelect(id)} aria-current={active === id ? "page" : undefined}>
          <Icon size={19} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
