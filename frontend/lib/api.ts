import type {
  ApiErrorEnvelope,
  DataResponse,
  Line,
  LineRoute,
  LineStop,
  PageResponse,
  Stop,
  Trip,
} from "@/types/transit";
import type { GeoBounds } from "@/lib/geo";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = "request_failed",
  ) {
    super(message);
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiError("Não foi possível conectar à API.", 0, "network_error");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorEnvelope | null;
    throw new ApiError(
      payload?.error.message ?? "A consulta não pôde ser concluída.",
      response.status,
      payload?.error.code,
    );
  }
  return response.json() as Promise<T>;
}

function params(values: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const result = query.toString();
  return result ? `?${result}` : "";
}

export const api = {
  listLines: (q = "", limit = 20, offset = 0) =>
    request<PageResponse<Line>>(`/lines${params({ q: q || undefined, limit, offset })}`),
  getLine: (routeId: string) => request<DataResponse<Line>>(`/lines/${routeId}`),
  getLineStops: (routeId: string, directionId?: string) =>
    request<DataResponse<LineStop[]>>(
      `/lines/${routeId}/stops${params({ direction_id: directionId })}`,
    ),
  getLineRoute: (routeId: string, directionId?: string) =>
    request<DataResponse<LineRoute>>(
      `/lines/${routeId}/route${params({ direction_id: directionId })}`,
    ),
  listLineTrips: (routeId: string) =>
    request<PageResponse<Trip>>(`/lines/${routeId}/trips${params({ limit: 200 })}`),
  listStops: (q = "", limit = 20, offset = 0) =>
    request<PageResponse<Stop>>(`/stops${params({ q: q || undefined, limit, offset })}`),
  listStopsInBounds: (bounds: GeoBounds, limit = 100) =>
    request<PageResponse<Stop>>(
      `/stops${params({
        min_lat: bounds.minLat,
        max_lat: bounds.maxLat,
        min_lon: bounds.minLon,
        max_lon: bounds.maxLon,
        limit,
      })}`,
    ),
  getStop: (stopId: string) => request<DataResponse<Stop>>(`/stops/${stopId}`),
};
