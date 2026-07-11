"use client";

import { useCallback, useEffect, useState } from "react";
import type { GeolocationState } from "@/types/mobility";

const INITIAL_STATE: GeolocationState = { status: "requesting", coordinates: null };

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>(INITIAL_STATE);

  const requestLocation = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setState({ status: "unsupported", coordinates: null });
      return;
    }

    setState((current) => ({ status: "requesting", coordinates: current.coordinates }));
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          status: "granted",
          coordinates: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
        });
      },
      (error) => {
        setState({
          status: error.code === error.PERMISSION_DENIED ? "denied" : "unavailable",
          coordinates: null,
        });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 },
    );
  }, []);

  useEffect(() => {
    const initialRequest = window.setTimeout(requestLocation, 0);
    return () => window.clearTimeout(initialRequest);
  }, [requestLocation]);

  return { ...state, requestLocation };
}
