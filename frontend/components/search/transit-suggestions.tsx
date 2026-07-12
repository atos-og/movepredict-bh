import { BusFront, ChevronRight, MapPin, Search } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";
import { FeedbackState } from "@/components/ui/feedback-state";
import type { GeocodedDestination } from "@/types/mobility";
import type { Line, Stop } from "@/types/transit";

type TransitSuggestionsProps = {
  query: string;
  destinations: GeocodedDestination[];
  geocodingAvailable: boolean;
  lines: Line[];
  stops: Stop[];
  loading: boolean;
  error: string | null;
  onDestinationSelect: (destination: GeocodedDestination) => void;
  onLineSelect: (line: Line) => void;
  onStopSelect: (stop: Stop) => void;
};

export function TransitSuggestions({
  query,
  destinations,
  geocodingAvailable,
  lines,
  stops,
  loading,
  error,
  onDestinationSelect,
  onLineSelect,
  onStopSelect,
}: TransitSuggestionsProps) {
  if (loading) {
    return <div className="suggestion-loading" aria-live="polite"><span className="spinner" />Buscando na base oficial...</div>;
  }

  if (error) {
    return <div className="suggestion-error" role="alert">{error}</div>;
  }

  const noTransitResults = !lines.length && !stops.length;
  if (geocodingAvailable && !destinations.length && noTransitResults) {
    return <FeedbackState icon={<Search size={23} />} title="Nenhum destino encontrado" description={`Não encontramos resultados para “${query}”.`} />;
  }

  return (
    <div className="suggestion-groups" id="destination-suggestions">
      {destinations.length > 0 && (
        <SuggestionGroup title="Destinos">
          {destinations.map((destination) => (
            <SuggestionButton key={destination.id} icon={<MapPin size={17} />} tone="destination" onClick={() => onDestinationSelect(destination)}>
              <strong><HighlightedText text={destination.label} query={query} /></strong>
              <small>{destination.description}</small>
            </SuggestionButton>
          ))}
        </SuggestionGroup>
      )}

      {!geocodingAvailable && (
        <div className="geocoding-note">
          <MapPin size={16} />
          <span><strong>Busca de lugares ainda não conectada</strong><small>Por enquanto, mostramos pontos e linhas oficiais relacionados ao termo.</small></span>
        </div>
      )}

      {stops.length > 0 && (
        <SuggestionGroup title="Pontos">
          {stops.map((stop) => (
            <SuggestionButton key={stop.stop_id} icon={<MapPin size={17} />} tone="stop" onClick={() => onStopSelect(stop)}>
              <strong><HighlightedText text={stop.stop_name} query={query} /></strong>
              <small>Ponto {stop.stop_code || stop.stop_id}</small>
            </SuggestionButton>
          ))}
        </SuggestionGroup>
      )}

      {lines.length > 0 && (
        <SuggestionGroup title="Linhas relacionadas">
          {lines.map((line) => (
            <SuggestionButton key={line.route_id} icon={<BusFront size={17} />} tone="line" onClick={() => onLineSelect(line)}>
              <strong><HighlightedText text={line.route_short_name || line.route_id} query={query} /></strong>
              <small><HighlightedText text={line.route_long_name || "Itinerário sem nome"} query={query} /></small>
            </SuggestionButton>
          ))}
        </SuggestionGroup>
      )}

      {!geocodingAvailable && noTransitResults && (
        <FeedbackState icon={<Search size={23} />} title="Nenhum ponto ou linha encontrado" description="A busca por endereços será ativada quando a geocodificação estiver conectada." />
      )}
    </div>
  );
}

function SuggestionGroup({ title, children }: { title: string; children: ReactNode }) {
  return <section className="suggestion-group"><h2>{title}</h2>{children}</section>;
}

function SuggestionButton({ icon, tone, onClick, children }: { icon: ReactNode; tone: string; onClick: () => void; children: ReactNode }) {
  return (
    <button onClick={onClick} onKeyDown={moveSuggestionFocus}>
      <span className={`suggestion-icon ${tone}`}>{icon}</span>
      <span>{children}</span>
      <ChevronRight size={17} />
    </button>
  );
}

function moveSuggestionFocus(event: KeyboardEvent<HTMLButtonElement>) {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  const container = event.currentTarget.closest("#destination-suggestions");
  if (!container) return;
  const buttons = Array.from(container.querySelectorAll<HTMLButtonElement>(".suggestion-group button"));
  const currentIndex = buttons.indexOf(event.currentTarget);
  const nextIndex = event.key === "ArrowDown" ? Math.min(currentIndex + 1, buttons.length - 1) : Math.max(currentIndex - 1, 0);
  event.preventDefault();
  buttons[nextIndex]?.focus();
}

function HighlightedText({ text, query }: { text: string; query: string }) {
  const normalized = query.trim();
  if (!normalized) return text;
  const index = text.toLocaleLowerCase("pt-BR").indexOf(normalized.toLocaleLowerCase("pt-BR"));
  if (index < 0) return text;
  return <>{text.slice(0, index)}<mark>{text.slice(index, index + normalized.length)}</mark>{text.slice(index + normalized.length)}</>;
}
