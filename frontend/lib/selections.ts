import type { RecentSelection } from "@/types/mobility";
import type { Line, Stop } from "@/types/transit";

export function toRecentLine(line: Line): RecentSelection {
  return {
    kind: "line",
    id: line.route_id,
    label: line.route_short_name || line.route_id,
    description: line.route_long_name || "Itinerario sem nome",
    value: line,
  };
}

export function toRecentStop(stop: Stop): RecentSelection {
  return {
    kind: "stop",
    id: stop.stop_id,
    label: stop.stop_name,
    description: `Ponto ${stop.stop_code || stop.stop_id}`,
    value: stop,
  };
}

export function selectionHref(selection: RecentSelection): string {
  if (selection.kind === "line") {
    return `/linha/${encodeURIComponent(selection.id)}`;
  }
  return `/pontos?stop=${encodeURIComponent(selection.id)}`;
}
