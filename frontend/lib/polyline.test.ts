import assert from "node:assert/strict";
import test from "node:test";
import { decodePolyline } from "./polyline.ts";

test("decodes a standard encoded polyline", () => {
  const points = decodePolyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@");
  assert.deepEqual(points, [
    { latitude: 38.5, longitude: -120.2 },
    { latitude: 40.7, longitude: -120.95 },
    { latitude: 43.252, longitude: -126.453 },
  ]);
});
