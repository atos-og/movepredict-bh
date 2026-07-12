import type { Coordinates, GeocodedDestination, JourneyPlan, JourneyPlannerProvider, JourneyPlanningResult, JourneyStep } from "@/types/mobility";

const PLANNER_URL = process.env.NEXT_PUBLIC_JOURNEY_PLANNER_URL?.replace(/\/$/, "");

type OtpLeg = {
  mode: string;
  duration: number;
  route?: string;
  routeShortName?: string;
  headsign?: string;
  from?: { name?: string };
  to?: { name?: string };
  startTime?: number;
  endTime?: number;
};

type OtpItinerary = { duration: number; walkTime?: number; transfers?: number; legs: OtpLeg[] };

class OpenTripPlannerProvider implements JourneyPlannerProvider {
  async plan(origin: Coordinates, destination: GeocodedDestination): Promise<JourneyPlanningResult> {
    if (!PLANNER_URL) return { status: "unavailable", plans: [] };
    const params = new URLSearchParams({
      fromPlace: `${origin.latitude},${origin.longitude}`,
      toPlace: `${destination.coordinates.latitude},${destination.coordinates.longitude}`,
      mode: "TRANSIT,WALK",
      numItineraries: "3",
      locale: "pt_BR",
    });
    try {
      const response = await fetch(`${PLANNER_URL}/plan?${params}`, { headers: { Accept: "application/json" } });
      if (!response.ok) return { status: "unavailable", plans: [] };
      const payload = await response.json() as { plan?: { itineraries?: OtpItinerary[] } };
      const itineraries = payload.plan?.itineraries || [];
      return { status: "available", plans: itineraries.map((item, index) => toPlan(item, destination, index)) };
    } catch {
      return { status: "unavailable", plans: [] };
    }
  }
}

function toPlan(item: OtpItinerary, destination: GeocodedDestination, index: number): JourneyPlan {
  const transitLegs = item.legs.filter((leg) => leg.mode !== "WALK");
  const firstTransit = transitLegs[0];
  return {
    id: `otp-${index}`,
    destinationLabel: destination.label,
    totalDurationMinutes: Math.ceil(item.duration / 60),
    walkingDurationMinutes: Math.ceil((item.walkTime || 0) / 60),
    lineIds: transitLegs.map((leg) => leg.route || leg.routeShortName || "").filter(Boolean),
    lineLabel: firstTransit?.routeShortName || firstTransit?.route || "Transporte publico",
    headsign: firstTransit?.headsign || destination.label,
    transferCount: item.transfers ?? Math.max(0, transitLegs.length - 1),
    scheduledDeparture: firstTransit?.startTime ? new Date(firstTransit.startTime).toISOString() : null,
    estimatedArrival: item.legs.at(-1)?.endTime ? new Date(item.legs.at(-1)!.endTime!).toISOString() : null,
    geometry: null,
    steps: item.legs.map((leg, legIndex): JourneyStep => ({
      id: `leg-${legIndex}`,
      kind: leg.mode === "WALK" ? "walk" : "bus",
      title: leg.mode === "WALK" ? `Caminhe ate ${leg.to?.name || "o proximo ponto"}` : `Linha ${leg.routeShortName || leg.route || ""}`,
      description: leg.mode === "WALK" ? leg.from?.name || null : leg.headsign || null,
      durationMinutes: Math.ceil(leg.duration / 60),
    })),
  };
}

export const journeyPlannerProvider: JourneyPlannerProvider = new OpenTripPlannerProvider();
