"use client";

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import type { Coordinates } from "@/types/mobility";
import type { LineRoute, LineStop, Stop } from "@/types/transit";
import type { VehiclePosition } from "@/types/realtime";

type Props = {
  selectedStop: Stop | null;
  lineStops: LineStop[];
  route: LineRoute | null;
  userLocation: Coordinates | null;
  nearbyStops: Stop[];
  vehicles: VehiclePosition[];
  showStops: boolean;
  showRoute: boolean;
  showVehicles: boolean;
  recenterToken: number;
  onStopSelect: (stop: Stop) => void;
};

const BH_CENTER: [number, number] = [-19.9167, -43.9345];

function ViewportController({
  selectedStop,
  route,
  userLocation,
  recenterToken,
}: Pick<Props, "selectedStop" | "route" | "userLocation" | "recenterToken">) {
  const map = useMap();

  useEffect(() => {
    if (selectedStop) {
      map.flyTo([selectedStop.stop_lat, selectedStop.stop_lon], 16, { duration: 0.7 });
    } else if (route?.geometry.coordinates.length) {
      const bounds = route.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    } else if (userLocation) {
      map.flyTo([userLocation.latitude, userLocation.longitude], 16, { duration: 0.7 });
    }
  }, [map, recenterToken, route, selectedStop, userLocation]);

  return null;
}

export default function MapView({
  selectedStop,
  lineStops,
  route,
  userLocation,
  nearbyStops,
  vehicles,
  showStops,
  showRoute,
  showVehicles,
  recenterToken,
  onStopSelect,
}: Props) {
  const positions = route?.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);

  return (
    <MapContainer center={BH_CENTER} zoom={13} className="map" zoomControl attributionControl>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ViewportController
        selectedStop={selectedStop}
        route={route}
        userLocation={userLocation}
        recenterToken={recenterToken}
      />
      {userLocation && (
        <>
          <CircleMarker
            center={[userLocation.latitude, userLocation.longitude]}
            radius={15}
            interactive={false}
            pathOptions={{ color: "#1c5aa6", weight: 1, fillColor: "#1c5aa6", fillOpacity: 0.16 }}
          />
          <CircleMarker
            center={[userLocation.latitude, userLocation.longitude]}
            radius={7}
            pathOptions={{ color: "#ffffff", weight: 3, fillColor: "#1c5aa6", fillOpacity: 1 }}
          >
            <Popup><strong>Sua localização</strong></Popup>
          </CircleMarker>
        </>
      )}
      {showRoute && positions && (
        <Polyline positions={positions} pathOptions={{ color: "#07866f", weight: 6, opacity: 0.88 }} />
      )}
      {showStops &&
        lineStops.map((stop) => (
          <CircleMarker
            key={`${stop.stop_id}-${stop.stop_sequence}`}
            center={[stop.stop_lat, stop.stop_lon]}
            radius={6}
            pathOptions={{ color: "#ffffff", weight: 2, fillColor: "#d64b32", fillOpacity: 1 }}
          >
            <Popup>
              <strong>{stop.stop_name}</strong>
              <br />Parada {stop.stop_sequence}
            </Popup>
          </CircleMarker>
        ))}
      {selectedStop && !lineStops.some((stop) => stop.stop_id === selectedStop.stop_id) && (
        <CircleMarker
          center={[selectedStop.stop_lat, selectedStop.stop_lon]}
          radius={9}
          pathOptions={{ color: "#ffffff", weight: 3, fillColor: "#d64b32", fillOpacity: 1 }}
        >
          <Popup>
            <strong>{selectedStop.stop_name}</strong>
            <br />Código {selectedStop.stop_code || selectedStop.stop_id}
          </Popup>
        </CircleMarker>
      )}
      {showStops &&
        !route &&
        nearbyStops
          .filter((stop) => stop.stop_id !== selectedStop?.stop_id)
          .map((stop) => (
            <CircleMarker
              key={`nearby-${stop.stop_id}`}
              center={[stop.stop_lat, stop.stop_lon]}
              radius={6}
              eventHandlers={{ click: () => onStopSelect(stop) }}
              pathOptions={{ color: "#ffffff", weight: 2, fillColor: "#d64b32", fillOpacity: 1 }}
            >
              <Popup><strong>{stop.stop_name}</strong><br />Ponto {stop.stop_code || stop.stop_id}</Popup>
            </CircleMarker>
          ))}
      {showVehicles &&
        vehicles.map((vehicle) => (
          <CircleMarker
            key={vehicle.vehicle_id}
            center={[vehicle.latitude, vehicle.longitude]}
            radius={8}
            pathOptions={{ color: "#ffffff", weight: 3, fillColor: "#1c5aa6", fillOpacity: 1 }}
          >
            <Popup>
              <strong>Veículo {vehicle.vehicle_id}</strong>
              <br />{vehicle.speed_kmh ? `${Math.round(vehicle.speed_kmh)} km/h` : "Velocidade indisponível"}
            </Popup>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}
