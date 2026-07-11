import { LocateFixed } from "lucide-react";

export function LocationLoadingSheet() {
  return <section className="location-loading-sheet"><span className="location-loading-icon"><LocateFixed size={24} /></span><div><strong>Obtendo sua localização...</strong><p>Isso pode levar alguns segundos.</p><span className="location-progress"><i /></span></div></section>;
}
