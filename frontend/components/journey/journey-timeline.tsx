import { BusFront, Flag, Footprints, MapPin, Navigation } from "lucide-react";
import type { JourneyStep } from "@/types/mobility";

const icons = { origin: Navigation, walk: Footprints, stop: MapPin, bus: BusFront, destination: Flag };

export function JourneyTimeline({ steps }: { steps: JourneyStep[] }) {
  return (
    <ol className="journey-timeline">
      {steps.map((step) => {
        const Icon = icons[step.kind];
        return <li key={step.id}><span><Icon size={17} /></span><div><strong>{step.title}</strong>{step.description && <p>{step.description}</p>}</div>{step.durationMinutes !== null && <small>{step.durationMinutes} min</small>}</li>;
      })}
    </ol>
  );
}
