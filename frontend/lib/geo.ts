import type { Coordinates } from "@/types/mobility";
import type { Stop } from "@/types/transit";

const EARTH_RADIUS_METERS = 6_371_000;

export type GeoBounds = {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
};

export function distanceInMeters(from: Coordinates, to: Coordinates): number {
  const latitudeDelta = toRadians(to.latitude - from.latitude);
  const longitudeDelta = toRadians(to.longitude - from.longitude);
  const fromLatitude = toRadians(from.latitude);
  const toLatitude = toRadians(to.latitude);
  const haversine =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(fromLatitude) * Math.cos(toLatitude) * Math.sin(longitudeDelta / 2) ** 2;

  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(haversine));
}

export function boundsAround(point: Coordinates, radiusMeters: number): GeoBounds {
  const latitudeDelta = radiusMeters / 111_320;
  const longitudeScale = Math.max(Math.cos(toRadians(point.latitude)), 0.2);
  const longitudeDelta = radiusMeters / (111_320 * longitudeScale);

  return {
    minLat: point.latitude - latitudeDelta,
    maxLat: point.latitude + latitudeDelta,
    minLon: point.longitude - longitudeDelta,
    maxLon: point.longitude + longitudeDelta,
  };
}

export function nearestStops(origin: Coordinates, stops: Stop[], limit = 3): Stop[] {
  return [...stops]
    .sort(
      (left, right) =>
        distanceInMeters(origin, stopCoordinates(left)) -
        distanceInMeters(origin, stopCoordinates(right)),
    )
    .slice(0, limit);
}

export function stopCoordinates(stop: Stop): Coordinates {
  return { latitude: stop.stop_lat, longitude: stop.stop_lon };
}

export function formatDistance(meters: number): string {
  if (meters < 1_000) return `${Math.max(1, Math.round(meters))} m`;
  return `${(meters / 1_000).toFixed(meters < 10_000 ? 1 : 0)} km`;
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}
