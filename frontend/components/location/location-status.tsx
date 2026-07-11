import { AlertCircle, LocateFixed, Navigation, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { GeolocationStatus } from "@/types/mobility";

type LocationStatusProps = {
  status: GeolocationStatus;
  onRetry: () => void;
};

const messages: Record<GeolocationStatus, { title: string; description: string }> = {
  idle: { title: "Sua localização", description: "Use sua posição para encontrar pontos próximos" },
  requesting: { title: "Localizando você", description: "Buscando sua posição atual..." },
  granted: { title: "Partindo da sua localização", description: "Mapa centralizado perto de você" },
  denied: { title: "Localização desativada", description: "Ative a permissão para ver pontos próximos" },
  unavailable: { title: "Localização indisponível", description: "Não foi possível obter sua posição agora" },
  timeout: { title: "A localização demorou demais", description: "Tente novamente ou continue sem sua posição" },
  manual: { title: "Origem escolhida", description: "Usando o ponto informado como partida" },
  unsupported: { title: "Localização não suportada", description: "Este navegador não oferece geolocalização" },
};

export function LocationStatus({ status, onRetry }: LocationStatusProps) {
  const message = messages[status];
  const Icon = status === "granted" ? Navigation : status === "requesting" ? LocateFixed : AlertCircle;

  return (
    <div className={`location-status location-status-${status}`} aria-live="polite">
      <span className="location-status-icon"><Icon size={17} /></span>
      <span className="location-status-copy"><strong>{message.title}</strong><small>{message.description}</small></span>
      {(status === "denied" || status === "unavailable" || status === "timeout") && (
        <Button variant="ghost" size="sm" onClick={onRetry} aria-label="Tentar localizar novamente" title="Tentar novamente">
          <RefreshCw size={16} />
        </Button>
      )}
    </div>
  );
}
