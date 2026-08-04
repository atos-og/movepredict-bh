import Image from "next/image";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export function AppHeader({ title = "MovePredict BH", backHref }: { title?: string; backHref?: string }) {
  return (
    <header className="roadmap-header">
      {backHref
        ? <Link className="roadmap-header-action" href={backHref} aria-label="Voltar"><ChevronLeft size={21} /></Link>
        : <span className="roadmap-logo"><Image alt="" src={`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/favicon.svg`} width={34} height={34} unoptimized /></span>}
      <h1>{title}</h1>
      <span aria-hidden="true" />
    </header>
  );
}
