import type { Line, Stop } from "@/types/transit";

export type Coordinates = {
  latitude: number;
  longitude: number;
};

export type GeolocationStatus =
  | "requesting"
  | "granted"
  | "denied"
  | "unavailable"
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

export type JourneyPlan = {
  destinationLabel: string;
  totalDurationMinutes: number;
  walkingDurationMinutes: number;
  lineIds: string[];
  alternatives: JourneyPlan[];
};

export interface DestinationProvider {
  search(query: string, near?: Coordinates): Promise<DestinationCandidate[]>;
}

export interface JourneyPlannerProvider {
  plan(origin: Coordinates, destination: DestinationCandidate): Promise<JourneyPlan[]>;
}
