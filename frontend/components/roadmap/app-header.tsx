import Link from "next/link";
import { Bell, BusFront, ChevronLeft } from "lucide-react";

export function AppHeader({ title = "MovePredict BH", backHref }: { title?: string; backHref?: string }) {
  return (
    <header className="roadmap-header">
      {backHref ? <Link className="roadmap-header-action" href={backHref} aria-label="Voltar"><ChevronLeft size={21} /></Link> : <span className="roadmap-logo"><BusFront size={19} /></span>}
      <strong>{title}</strong>
      <button className="roadmap-header-action" type="button" aria-label="Notificações"><Bell size={18} /></button>
    </header>
  );
}
