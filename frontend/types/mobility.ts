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

export type JourneyPreference = "quickest" | "less_walking" | "fewer_transfers";

export type JourneyStop = {
  stopId: string;
  name: string;
  coordinates: Coordinates;
};

export type JourneyPlan = {
  id: string;
  preference: JourneyPreference;
  destinationLabel: string;
  totalDurationMinutes: number;
  walkingDurationMinutes: number;
  walkingDistanceMeters: number;
  lineIds: string[];
  lineLabel: string;
  headsign: string;
  transferCount: number;
  scheduledDeparture: string | null;
  estimatedArrival: string | null;
  geometry: Coordinates[];
  realtimeStatus: "live" | "scheduled" | "unavailable";
  nextBusArrival: string | null;
  uncertaintySeconds: number | null;
  steps: JourneyStep[];
};

export type JourneyStep = {
  id: string;
  kind: "origin" | "walk" | "stop" | "bus" | "destination";
  title: string;
  description: string | null;
  durationMinutes: number | null;
  distanceMeters: number;
  routeId: string | null;
  routeShortName: string | null;
  tripId: string | null;
  headsign: string | null;
  fromStop: JourneyStop | null;
  toStop: JourneyStop | null;
  intermediateStops: JourneyStop[];
  scheduledStart: string | null;
  scheduledEnd: string | null;
  geometry: Coordinates[];
};

export type JourneyPlanningResult =
  | { status: "available"; plans: JourneyPlan[] }
  | { status: "unavailable"; plans: [] };

export interface DestinationProvider {
  search(query: string, near?: Coordinates): Promise<GeocodingSearchResult>;
}

export interface JourneyPlannerProvider {
  plan(
    origin: Coordinates,
    destination: GeocodedDestination,
    preference?: JourneyPreference,
  ): Promise<JourneyPlanningResult>;
}

export type GeocodingApiResponse = {
  data: Array<{
    id: string;
    kind: GeocodedDestinationKind;
    label: string;
    description: string;
    coordinates: Coordinates;
  }>;
  meta: { provider: "nominatim"; attribution: string; cached: boolean };
};

export type JourneyPlanApiResponse = {
  data: Array<{
    id: string;
    preference: JourneyPreference;
    total_duration_minutes: number;
    walking_duration_minutes: number;
    walking_distance_meters: number;
    transfer_count: number;
    scheduled_departure: string | null;
    estimated_arrival: string | null;
    steps: Array<{
      id: string;
      kind: "walk" | "bus";
      title: string;
      description: string | null;
      duration_minutes: number;
      distance_meters: number;
      route_id: string | null;
      route_short_name: string | null;
      route_long_name: string | null;
      trip_id: string | null;
      headsign: string | null;
      from_stop: { stop_id: string; name: string; coordinates: Coordinates } | null;
      to_stop: { stop_id: string; name: string; coordinates: Coordinates } | null;
      intermediate_stops: Array<{ stop_id: string; name: string; coordinates: Coordinates }>;
      scheduled_start: string | null;
      scheduled_end: string | null;
      geometry: string | null;
      realtime: boolean;
    }>;
  }>;
  meta: { provider: "opentripplanner"; realtime_applied: boolean; generated_at: string };
};
