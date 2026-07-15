export type VehicleStatus = "in_transit" | "stopped" | "unknown";

export type VehiclePosition = {
  vehicle_id: string;
  route_id: string | null;
  trip_id: string | null;
  latitude: number;
  longitude: number;
  bearing: number | null;
  speed_kmh: number | null;
  observed_at: string;
  status: VehicleStatus;
};

export type ArrivalPrediction = {
  stop_id: string;
  route_id: string;
  trip_id: string | null;
  vehicle_id: string | null;
  predicted_arrival: string;
  generated_at: string;
  uncertainty_seconds: number | null;
  model_version: string | null;
};

export type RealtimeMeta = {
  generated_at: string;
  count: number;
  status: "live" | "empty" | "stale";
  stale: boolean;
  stale_after_seconds: number;
};

export type RealtimeResponse<T> = {
  data: T[];
  meta: RealtimeMeta;
};

export type ServiceAlert = {
  id: string;
  title: string;
  description: string | null;
  url: string | null;
  cause: string | null;
  effect: string | null;
  route_ids: string[];
  stop_ids: string[];
  active_from: string | null;
  active_until: string | null;
};

export type ServiceAlertResponse = {
  data: ServiceAlert[];
  meta: {
    generated_at: string;
    count: number;
    status: "live" | "empty" | "unavailable";
    source_configured: boolean;
  };
};

export interface RealtimeProvider {
  listVehicles(routeId?: string): Promise<VehiclePosition[]>;
  listPredictions(stopId: string, routeId?: string): Promise<ArrivalPrediction[]>;
}
