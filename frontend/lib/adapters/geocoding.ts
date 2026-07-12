import type { Coordinates, DestinationProvider, GeocodingSearchResult } from "@/types/mobility";

const GEOCODING_URL = process.env.NEXT_PUBLIC_GEOCODING_URL?.replace(/\/$/, "");

class HttpGeocodingProvider implements DestinationProvider {
  async search(query: string, near?: Coordinates): Promise<GeocodingSearchResult> {
    if (!GEOCODING_URL || query.trim().length < 2) return { status: "unavailable", data: [] };
    const params = new URLSearchParams({
      q: `${query.trim()}, Belo Horizonte, MG`,
      format: "jsonv2",
      addressdetails: "1",
      limit: "6",
      countrycodes: "br",
    });
    if (near) params.set("viewbox", `${near.longitude - 0.3},${near.latitude + 0.3},${near.longitude + 0.3},${near.latitude - 0.3}`);
    try {
      const response = await fetch(`${GEOCODING_URL}/search?${params}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return { status: "unavailable", data: [] };
      const rows = await response.json() as Array<{ place_id: number; lat: string; lon: string; display_name: string; type?: string; name?: string }>;
      return {
        status: "available",
        data: rows.map((row) => ({
          id: String(row.place_id),
          kind: row.type === "neighbourhood" ? "neighborhood" : row.type === "house" ? "address" : "destination",
          label: row.name || row.display_name.split(",")[0],
          description: row.display_name,
          coordinates: { latitude: Number(row.lat), longitude: Number(row.lon) },
        })),
      };
    } catch {
      return { status: "unavailable", data: [] };
    }
  }
}

export const geocodingProvider: DestinationProvider = new HttpGeocodingProvider();
