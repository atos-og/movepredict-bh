export type Line = {
  route_id: string;
  route_short_name: string | null;
  route_long_name: string | null;
  route_type: number | null;
  route_color: string | null;
  route_text_color: string | null;
};

export type Stop = {
  stop_id: string;
  stop_code: string | null;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
  wheelchair_boarding: number | null;
};

export type LineStop = Stop & {
  stop_sequence: number;
  arrival_time: string | null;
  departure_time: string | null;
};

export type LineRoute = {
  route_id: string;
  trip_id: string;
  shape_id: string;
  direction_id: string | null;
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
};

export type PageMeta = {
  total: number;
  returned: number;
  limit: number;
  offset: number;
};

export type PageResponse<T> = { data: T[]; meta: PageMeta };
export type DataResponse<T> = { data: T };

export type ApiErrorEnvelope = {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: Record<string, unknown>;
  };
};
