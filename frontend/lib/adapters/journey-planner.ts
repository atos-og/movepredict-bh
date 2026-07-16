import { api } from "@/lib/api";
import { decodePolyline } from "@/lib/polyline";
import type {
  Coordinates,
  GeocodedDestination,
  JourneyPlan,
  JourneyPlanApiResponse,
  JourneyPlannerProvider,
  JourneyPlanningResult,
  JourneyPreference,
  JourneyStop,
} from "@/types/mobility";

class ApiJourneyPlannerProvider implements JourneyPlannerProvider {
  async plan(
    origin: Coordinates,
    destination: GeocodedDestination,
    preference: JourneyPreference = "quickest",
  ): Promise<JourneyPlanningResult> {
    try {
      const response = await api.planJourney(
        origin.latitude,
        origin.longitude,
        destination.coordinates.latitude,
        destination.coordinates.longitude,
        preference,
      );
      const plans = response.data.map((plan) => toPlan(plan, destination));
      const arrivalRequests = new Map<string, ReturnType<typeof api.listArrivals>>();
      const enriched = await Promise.all(plans.map(async (plan) => {
        const firstBus = plan.steps.find((step) => step.kind === "bus" && step.fromStop);
        if (!firstBus?.fromStop) return plan;
        const key = `${firstBus.fromStop.stopId}:${firstBus.routeId || ""}`;
        if (!arrivalRequests.has(key)) {
          arrivalRequests.set(key, api.listArrivals(firstBus.fromStop.stopId, firstBus.routeId || undefined));
        }
        try {
          const arrivals = await arrivalRequests.get(key)!;
          const prediction = arrivals.data.find((item) => !firstBus.routeId || item.route_id === firstBus.routeId);
          if (!prediction || arrivals.meta.status !== "live") return plan;
          return {
            ...plan,
            realtimeStatus: "live" as const,
            nextBusArrival: prediction.predicted_arrival,
            uncertaintySeconds: prediction.uncertainty_seconds,
          };
        } catch {
          return plan;
        }
      }));
      return { status: "available", plans: enriched };
    } catch {
      return { status: "unavailable", plans: [] };
    }
  }
}

function toPlan(
  raw: JourneyPlanApiResponse["data"][number],
  destination: GeocodedDestination,
): JourneyPlan {
  const steps = raw.steps.map((step) => ({
    id: step.id,
    kind: step.kind,
    title: step.title,
    description: step.description,
    durationMinutes: step.duration_minutes,
    distanceMeters: step.distance_meters,
    routeId: step.route_id,
    routeShortName: step.route_short_name,
    tripId: step.trip_id,
    headsign: step.headsign,
    fromStop: toStop(step.from_stop),
    toStop: toStop(step.to_stop),
    intermediateStops: step.intermediate_stops.map((stop) => toStop(stop)!),
    scheduledStart: step.scheduled_start,
    scheduledEnd: step.scheduled_end,
    geometry: decodePolyline(step.geometry),
  }));
  const transitSteps = steps.filter((step) => step.kind === "bus");
  const firstTransit = transitSteps[0];
  return {
    id: raw.id,
    preference: raw.preference,
    destinationLabel: destination.label,
    totalDurationMinutes: raw.total_duration_minutes,
    walkingDurationMinutes: raw.walking_duration_minutes,
    walkingDistanceMeters: raw.walking_distance_meters,
    lineIds: transitSteps.map((step) => step.routeId).filter((value): value is string => Boolean(value)),
    lineLabel: transitSteps.map((step) => step.routeShortName || step.routeId).filter(Boolean).join(" + ") || "Caminhada",
    headsign: firstTransit?.headsign || destination.label,
    transferCount: raw.transfer_count,
    scheduledDeparture: raw.scheduled_departure,
    estimatedArrival: raw.estimated_arrival,
    geometry: steps.flatMap((step) => step.geometry),
    realtimeStatus: raw.scheduled_departure ? "scheduled" : "unavailable",
    nextBusArrival: null,
    uncertaintySeconds: null,
    steps,
  };
}

function toStop(
  stop: JourneyPlanApiResponse["data"][number]["steps"][number]["from_stop"],
): JourneyStop | null {
  if (!stop) return null;
  return { stopId: stop.stop_id, name: stop.name, coordinates: stop.coordinates };
}

export const journeyPlannerProvider: JourneyPlannerProvider = new ApiJourneyPlannerProvider();
