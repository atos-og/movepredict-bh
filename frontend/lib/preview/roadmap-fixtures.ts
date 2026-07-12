import type { JourneyPlan } from "@/types/mobility";
import type { VehiclePosition } from "@/types/realtime";

export const previewJourney: JourneyPlan = {
  id: "visual-preview-1170",
  destinationLabel: "Savassi",
  totalDurationMinutes: 32,
  walkingDurationMinutes: 9,
  lineIds: ["1170"],
  lineLabel: "1170",
  headsign: "Santa Lúcia / Mangabeiras",
  transferCount: 0,
  scheduledDeparture: "09:12",
  estimatedArrival: null,
  geometry: null,
  steps: [
    { id: "origin", kind: "origin", title: "Partindo da sua localização", description: "Agora", durationMinutes: null },
    { id: "walk", kind: "walk", title: "Caminhe até o ponto", description: "Av. Amazonas, 5075 · 450 m", durationMinutes: 6 },
    { id: "bus", kind: "bus", title: "Linha 1170", description: "Santa Lúcia / Mangabeiras", durationMinutes: 22 },
    { id: "stop", kind: "stop", title: "Desça na Savassi", description: "12 paradas", durationMinutes: null },
    { id: "final-walk", kind: "walk", title: "Caminhe até o destino", description: "Praça Diogo de Vasconcelos · 200 m", durationMinutes: 3 },
    { id: "destination", kind: "destination", title: "Chegada", description: "09:42", durationMinutes: null },
  ],
};

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
