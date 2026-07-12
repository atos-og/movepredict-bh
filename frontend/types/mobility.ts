import type { Line, Stop } from "@/types/transit";

export type Coordinates = {
  latitude: number;
  longitude: number;
};

export type GeolocationStatus =
  | "idle"
  | "requesting"
  | "granted"
  | "denied"
  | "unavailable"
  | "timeout"
  | "manual"
  | "unsupported";

export type GeolocationState = {
  status: GeolocationStatus;
  coordinates: Coordinates | null;
};

export type RecentSelection =
  | { kind: "line"; id: string; label: string; description: string; value: Line }
  | { kind: "stop"; id: string; label: string; description: string; value: Stop };

export type DestinationCandidate =
  | { kind: "line"; value: Line }
  | { kind: "stop"; value: Stop };

export type GeocodedDestinationKind = "destination" | "neighborhood" | "landmark" | "address";

export type GeocodedDestination = {
  id: string;
  kind: GeocodedDestinationKind;
  label: string;
  description: string;
  coordinates: Coordinates;
};

export type GeocodingSearchResult =
  | { status: "available"; data: GeocodedDestination[] }
  | { status: "unavailable"; data: [] };

export type JourneyPlan = {
  id: string;
  destinationLabel: string;
  totalDurationMinutes: number;
  walkingDurationMinutes: number;
  lineIds: string[];
  lineLabel: string;
  headsign: string;
  transferCount: number;
  scheduledDeparture: string | null;
  estimatedArrival: string | null;
  geometry: [number, number][] | null;
  steps: JourneyStep[];
};

export type JourneyStep = {
  id: string;
  kind: "origin" | "walk" | "stop" | "bus" | "destination";
  title: string;
  description: string | null;
  durationMinutes: number | null;
};

export type JourneyPlanningResult =
  | { status: "available"; plans: JourneyPlan[] }
  | { status: "unavailable"; plans: [] };

export interface DestinationProvider {
  search(query: string, near?: Coordinates): Promise<GeocodingSearchResult>;
}

export interface JourneyPlannerProvider {
  plan(origin: Coordinates, destination: GeocodedDestination): Promise<JourneyPlanningResult>;
}
