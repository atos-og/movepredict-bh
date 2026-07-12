import assert from "node:assert/strict";
import test from "node:test";
import { boundsAround, distanceInMeters, formatDistance, nearestStops } from "./geo.ts";
import type { Stop } from "@/types/transit";

const origin = { latitude: -19.9167, longitude: -43.9345 };

test("distanceInMeters returns zero for the same point", () => {
  assert.equal(distanceInMeters(origin, origin), 0);
});

test("boundsAround contains the origin", () => {
  const bounds = boundsAround(origin, 1_500);
  assert.ok(bounds.minLat < origin.latitude);
  assert.ok(bounds.maxLat > origin.latitude);
  assert.ok(bounds.minLon < origin.longitude);
  assert.ok(bounds.maxLon > origin.longitude);
});

test("nearestStops orders stops by geographic distance", () => {
  const far = makeStop("far", -19.95, -43.97);
  const near = makeStop("near", -19.917, -43.9345);
  assert.deepEqual(nearestStops(origin, [far, near], 1).map((stop) => stop.stop_id), ["near"]);
});

test("formatDistance uses meters and kilometers", () => {
  assert.equal(formatDistance(480), "480 m");
  assert.equal(formatDistance(1_540), "1.5 km");
});

function makeStop(stopId: string, latitude: number, longitude: number): Stop {
  return {
    stop_id: stopId,
    stop_code: stopId,
    stop_name: stopId,
    stop_lat: latitude,
    stop_lon: longitude,
    wheelchair_boarding: null,
  };
}
