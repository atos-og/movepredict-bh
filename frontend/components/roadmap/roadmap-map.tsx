"use client";

import dynamic from "next/dynamic";
import type { Coordinates } from "@/types/mobility";
import type { LineRoute, LineStop, Stop } from "@/types/transit";
import type { VehiclePosition } from "@/types/realtime";

const MapView = dynamic(() => import("@/components/map-view"), { ssr: false, loading: () => <div className="roadmap-map-loading" /> });

export function RoadmapMap({ userLocation = null, nearbyStops = [], lineStops = [], route = null, vehicles = [], showVehicles = false }: { userLocation?: Coordinates | null; nearbyStops?: Stop[]; lineStops?: LineStop[]; route?: LineRoute | null; vehicles?: VehiclePosition[]; showVehicles?: boolean }) {
  return <div className="roadmap-map"><MapView selectedStop={null} lineStops={lineStops} route={route} userLocation={userLocation} nearbyStops={nearbyStops} vehicles={vehicles} showRoute={Boolean(route)} showStops showVehicles={showVehicles} recenterToken={0} onStopSelect={() => undefined} /></div>;
}
