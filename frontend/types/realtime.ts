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

export interface RealtimeProvider {
  listVehicles(routeId?: string): Promise<VehiclePosition[]>;
  listPredictions(stopId: string, routeId?: string): Promise<ArrivalPrediction[]>;
}
