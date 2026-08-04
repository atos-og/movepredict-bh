import type { JourneyPlan } from "@/types/mobility";
import type { VehiclePosition } from "@/types/realtime";

export const previewJourney: JourneyPlan = {
  id: "visual-preview-1170",
  preference: "quickest",
  destinationLabel: "Savassi",
  totalDurationMinutes: 32,
  walkingDurationMinutes: 9,
  walkingDistanceMeters: 650,
  lineIds: ["1170"],
  lineLabel: "1170",
  headsign: "Santa Lucia / Mangabeiras",
  transferCount: 0,
  scheduledDeparture: "09:12",
  estimatedArrival: null,
  geometry: [],
  realtimeStatus: "scheduled",
  nextBusArrival: null,
  uncertaintySeconds: null,
  steps: [
    previewStep("origin", "origin", "Partindo da sua localizacao", "Agora", null),
    previewStep("walk", "walk", "Caminhe ate o ponto", "Av. Amazonas, 5075 - 450 m", 6),
    { ...previewStep("bus", "bus", "Linha 1170", "Santa Lucia / Mangabeiras", 22), routeId: "1170", routeShortName: "1170" },
    previewStep("stop", "stop", "Desca na Savassi", "12 paradas", null),
    previewStep("final-walk", "walk", "Caminhe ate o destino", "Praca Diogo de Vasconcelos - 200 m", 3),
    previewStep("destination", "destination", "Chegada", "09:42", null),
  ],
};

function previewStep(id: string, kind: JourneyPlan["steps"][number]["kind"], title: string, description: string, durationMinutes: number | null): JourneyPlan["steps"][number] {
  return { id, kind, title, description, durationMinutes, distanceMeters: 0, routeId: null, routeShortName: null, tripId: null, headsign: null, fromStop: null, toStop: null, intermediateStops: [], scheduledStart: null, scheduledEnd: null, geometry: [] };
}

export const previewVehicle: VehiclePosition = {
  vehicle_id: "preview-bus-1170",
  route_id: "1170",
  trip_id: "visual-preview",
  latitude: -19.9286,
  longitude: -43.9398,
  bearing: 138,
  speed_kmh: null,
  observed_at: "visual-preview",
  status: "in_transit",
};
