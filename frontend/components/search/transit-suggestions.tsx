import { BusFront, ChevronRight, MapPin, Search } from "lucide-react";
import { FeedbackState } from "@/components/ui/feedback-state";
import type { Line, Stop } from "@/types/transit";

type TransitSuggestionsProps = {
  query: string;
  lines: Line[];
  stops: Stop[];
  loading: boolean;
  error: string | null;
  onLineSelect: (line: Line) => void;
  onStopSelect: (stop: Stop) => void;
};

export function TransitSuggestions({
  query,
  lines,
  stops,
  loading,
  error,
  onLineSelect,
  onStopSelect,
}: TransitSuggestionsProps) {
  if (loading) {
    return <div className="suggestion-loading" aria-live="polite"><span className="spinner" />Buscando na base oficial...</div>;
  }

  if (error) {
    return <div className="suggestion-error" role="alert">{error}</div>;
  }

  if (!lines.length && !stops.length) {
    return (
      <FeedbackState
        icon={<Search size={23} />}
        title="Destino ainda não disponível"
        description={`Não encontramos “${query}” entre as linhas e os pontos oficiais. Endereços dependerão da futura integração de geocodificação.`}
      />
    );
  }

  return (
    <div className="suggestion-groups">
      {lines.length > 0 && (
        <section className="suggestion-group">
          <h2>Linhas</h2>
          {lines.map((line) => (
            <button key={line.route_id} onClick={() => onLineSelect(line)}>
              <span className="suggestion-icon line"><BusFront size={17} /></span>
              <span><strong>{line.route_short_name || line.route_id}</strong><small>{line.route_long_name || "Itinerário sem nome"}</small></span>
              <ChevronRight size={17} />
            </button>
          ))}
        </section>
      )}
      {stops.length > 0 && (
        <section className="suggestion-group">
          <h2>Pontos</h2>
          {stops.map((stop) => (
            <button key={stop.stop_id} onClick={() => onStopSelect(stop)}>
              <span className="suggestion-icon stop"><MapPin size={17} /></span>
              <span><strong>{stop.stop_name}</strong><small>Ponto {stop.stop_code || stop.stop_id}</small></span>
              <ChevronRight size={17} />
            </button>
          ))}
        </section>
      )}
    </div>
  );
}
