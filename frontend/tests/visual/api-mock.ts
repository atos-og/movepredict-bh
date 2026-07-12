import type { Page } from "@playwright/test";

const line = { route_id: "989341", route_short_name: "1170", route_long_name: "Santa Lucia / Mangabeiras", route_type: 3, route_color: "102a43", route_text_color: "ffffff" };
const stops = [
  { stop_id: "s1", stop_code: "1001", stop_name: "Av. Amazonas, 5075", stop_lat: -19.921, stop_lon: -43.955, wheelchair_boarding: 1 },
  { stop_id: "s2", stop_code: "1002", stop_name: "Savassi", stop_lat: -19.938, stop_lon: -43.936, wheelchair_boarding: 1 },
  { stop_id: "s3", stop_code: "1003", stop_name: "Praca da Liberdade", stop_lat: -19.932, stop_lon: -43.938, wheelchair_boarding: 0 },
];
const lineStops = stops.map((stop, index) => ({ ...stop, stop_sequence: index + 1, arrival_time: `09:${String(5 + index * 8).padStart(2, "0")}:00`, departure_time: `09:${String(6 + index * 8).padStart(2, "0")}:00` }));

export async function mockTransitApi(page: Page) {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    let payload: unknown;
    if (url.pathname === "/lines") payload = { data: [line], meta: { total: 1, returned: 1, limit: 20, offset: 0 } };
    else if (url.pathname === "/lines/989341") payload = { data: line };
    else if (url.pathname.endsWith("/stops") && url.pathname.startsWith("/lines/")) payload = { data: lineStops };
    else if (url.pathname.endsWith("/route")) payload = { data: { route_id: "989341", trip_id: "t1", direction_id: "0", geometry: { type: "LineString", coordinates: stops.map((stop) => [stop.stop_lon, stop.stop_lat]) } } };
    else if (url.pathname === "/stops") payload = { data: stops, meta: { total: 3, returned: 3, limit: 80, offset: 0 } };
    else if (url.pathname.startsWith("/realtime/")) payload = { data: [], meta: { generated_at: "2026-07-12T12:00:00Z", count: 0, stale: true, stale_after_seconds: 120 } };
    else payload = { error: { code: "not_found", message: "Fixture nao encontrada" } };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
  });
}
