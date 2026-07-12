"use client";

import { divIcon } from "leaflet";
import { Marker, Popup } from "react-leaflet";
import type { VehiclePosition } from "@/types/realtime";

export function MovingBusMarker({ vehicle }: { vehicle: VehiclePosition }) {
  const bearing = vehicle.bearing ?? 0;
  const icon = divIcon({
    className: "moving-bus-marker-shell",
    html: `<span class="moving-bus-marker" style="--bus-bearing:${bearing}deg" aria-hidden="true"><span class="bus-window"></span><span class="bus-wheel left"></span><span class="bus-wheel right"></span></span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });

  return (
    <Marker position={[vehicle.latitude, vehicle.longitude]} icon={icon}>
      <Popup><strong>Linha {vehicle.route_id || "não identificada"}</strong><br />Veículo {vehicle.vehicle_id}<br />Última posição: {new Date(vehicle.observed_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</Popup>
    </Marker>
  );
}
