import type {
  ApiErrorEnvelope,
  DataResponse,
  Line,
  LineRoute,
  LineStop,
  PageResponse,
  Stop,
} from "@/types/transit";

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
  listLines: (q = "", limit = 20) =>
    request<PageResponse<Line>>(`/lines${params({ q: q || undefined, limit })}`),
  getLine: (routeId: string) => request<DataResponse<Line>>(`/lines/${routeId}`),
  getLineStops: (routeId: string) =>
    request<DataResponse<LineStop[]>>(`/lines/${routeId}/stops`),
  getLineRoute: (routeId: string) =>
    request<DataResponse<LineRoute>>(`/lines/${routeId}/route`),
  listStops: (q = "", limit = 20) =>
    request<PageResponse<Stop>>(`/stops${params({ q: q || undefined, limit })}`),
  getStop: (stopId: string) => request<DataResponse<Stop>>(`/stops/${stopId}`),
};
