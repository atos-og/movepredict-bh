import { AlertCircle, LocateFixed, Navigation } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { GeolocationStatus } from "@/types/mobility";

type LocationPermissionCardProps = {
  status: GeolocationStatus;
  onRequest: () => void;
  onSkip: () => void;
};

export function LocationPermissionCard({ status, onRequest, onSkip }: LocationPermissionCardProps) {
  const requesting = status === "requesting";
  const failed = status === "denied" || status === "unavailable" || status === "timeout" || status === "unsupported";

  return (
    <section className="location-permission-card" aria-live="polite">
      <span className={`permission-illustration ${failed ? "failed" : ""}`} aria-hidden="true">
        {failed ? <AlertCircle size={30} /> : requesting ? <LocateFixed size={30} /> : <Navigation size={30} />}
      </span>
      <div className="permission-copy">
        <h2>{requesting ? "Obtendo sua localização..." : failed ? "Não conseguimos usar sua localização" : "Encontre a melhor rota saindo de onde você está"}</h2>
        <p>
          {requesting
            ? "Isso pode levar alguns segundos."
            : failed
              ? "Você pode tentar novamente ou continuar explorando linhas e pontos."
              : "Usaremos sua localização para encontrar o ponto mais próximo e preparar sua viagem."}
        </p>
      </div>
      {!requesting && (
        <Button className="permission-primary" onClick={onRequest}>
          <LocateFixed size={18} /> {failed ? "Tentar novamente" : "Usar minha localização"}
        </Button>
      )}
      <Button variant="ghost" onClick={onSkip}>{requesting ? "Continuar sem esperar" : "Agora não"}</Button>
    </section>
  );
}
