"use client";

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { MovingBusMarker } from "@/components/map/moving-bus-marker";
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
  journeyGeometry?: Coordinates[];
};

const BH_CENTER: [number, number] = [-19.9167, -43.9345];

function MapAccessibility() {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    container.setAttribute("role", "region");
    container.setAttribute("aria-label", "Mapa de mobilidade de Belo Horizonte");
  }, [map]);

  return null;
}

function ViewportController({
  selectedStop,
  route,
  userLocation,
  recenterToken,
  journeyGeometry = [],
}: Pick<Props, "selectedStop" | "route" | "userLocation" | "recenterToken" | "journeyGeometry">) {
  const map = useMap();

  useEffect(() => {
    if (selectedStop) {
      map.flyTo([selectedStop.stop_lat, selectedStop.stop_lon], 16, { duration: 0.7 });
    } else if (journeyGeometry.length) {
      map.fitBounds(journeyGeometry.map((point) => [point.latitude, point.longitude] as [number, number]), { padding: [36, 36], maxZoom: 16 });
    } else if (route?.geometry.coordinates.length) {
      const bounds = route.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    } else if (userLocation) {
      map.flyTo([userLocation.latitude, userLocation.longitude], 16, { duration: 0.7 });
    }
  }, [journeyGeometry, map, recenterToken, route, selectedStop, userLocation]);

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
  journeyGeometry = [],
}: Props) {
  const positions = route?.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);

  return (
    <MapContainer center={BH_CENTER} zoom={13} className="map" zoomControl attributionControl>
      <MapAccessibility />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ViewportController
        selectedStop={selectedStop}
        route={route}
        userLocation={userLocation}
        recenterToken={recenterToken}
        journeyGeometry={journeyGeometry}
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
      {journeyGeometry.length > 1 && (
        <Polyline positions={journeyGeometry.map((point) => [point.latitude, point.longitude])} pathOptions={{ color: "#1261c9", weight: 6, opacity: 0.9 }} />
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
        vehicles.map((vehicle) => <MovingBusMarker key={vehicle.vehicle_id} vehicle={vehicle} />)}
    </MapContainer>
  );
}
