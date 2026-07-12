import type { Coordinates, GeocodedDestination, JourneyPlannerProvider, JourneyPlanningResult } from "@/types/mobility";

class UnavailableJourneyPlannerProvider implements JourneyPlannerProvider {
  async plan(origin: Coordinates, destination: GeocodedDestination): Promise<JourneyPlanningResult> {
    void origin;
    void destination;
    return { status: "unavailable", plans: [] };
  }
}

export const journeyPlannerProvider: JourneyPlannerProvider = new UnavailableJourneyPlannerProvider();
