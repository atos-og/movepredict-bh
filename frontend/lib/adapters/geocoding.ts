import type { Coordinates, DestinationProvider, GeocodingSearchResult } from "@/types/mobility";

class UnavailableGeocodingProvider implements DestinationProvider {
  async search(query: string, near?: Coordinates): Promise<GeocodingSearchResult> {
    void query;
    void near;
    return { status: "unavailable", data: [] };
  }
}

export const geocodingProvider: DestinationProvider = new UnavailableGeocodingProvider();
