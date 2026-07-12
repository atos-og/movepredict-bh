import { BusFront, Clock3, Footprints, MoveRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { JourneyPlan } from "@/types/mobility";

export function JourneyOptionCard({ plan, primary = false, onSelect }: { plan: JourneyPlan; primary?: boolean; onSelect: () => void }) {
  return (
    <article className={`journey-option-card ${primary ? "primary" : ""}`}>
      <header><span>{primary ? "Melhor opção agora" : "Outra opção"}</span><strong>{plan.totalDurationMinutes} min</strong></header>
      <div className="journey-option-metrics">
        <span><Footprints size={16} />{plan.walkingDurationMinutes} min a pé</span>
        <span><BusFront size={16} />{plan.lineLabel}</span>
        <span><Clock3 size={16} />{plan.scheduledDeparture ? `Partida programada ${plan.scheduledDeparture}` : "Horário programado indisponível"}</span>
      </div>
      <p>{plan.headsign}</p>
      <Button onClick={onSelect}>Ver detalhes da rota <MoveRight size={17} /></Button>
    </article>
  );
}
