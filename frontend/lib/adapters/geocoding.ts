import { api } from "@/lib/api";
import type { DestinationProvider, GeocodingSearchResult } from "@/types/mobility";

class ApiGeocodingProvider implements DestinationProvider {
  async search(query: string): Promise<GeocodingSearchResult> {
    if (query.trim().length < 2) return { status: "unavailable", data: [] };
    try {
      const response = await api.searchDestinations(query.trim());
      return { status: "available", data: response.data };
    } catch {
      return { status: "unavailable", data: [] };
    }
  }
}

export const geocodingProvider: DestinationProvider = new ApiGeocodingProvider();
