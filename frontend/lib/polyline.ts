import type { Coordinates } from "@/types/mobility";

export function decodePolyline(encoded: string | null): Coordinates[] {
  if (!encoded) return [];
  const points: Coordinates[] = [];
  let index = 0;
  let latitude = 0;
  let longitude = 0;

  while (index < encoded.length) {
    const latitudeResult = decodeValue(encoded, index);
    index = latitudeResult.nextIndex;
    latitude += latitudeResult.value;
    const longitudeResult = decodeValue(encoded, index);
    index = longitudeResult.nextIndex;
    longitude += longitudeResult.value;
    points.push({ latitude: latitude / 1e5, longitude: longitude / 1e5 });
  }
  return points;
}

function decodeValue(encoded: string, start: number): { value: number; nextIndex: number } {
  let result = 0;
  let shift = 0;
  let index = start;
  let byte: number;
  do {
    byte = encoded.charCodeAt(index++) - 63;
    result |= (byte & 0x1f) << shift;
    shift += 5;
  } while (byte >= 0x20 && index < encoded.length);
  return {
    value: result & 1 ? ~(result >> 1) : result >> 1,
    nextIndex: index,
  };
}
