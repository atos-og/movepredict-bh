"use client";

import { useCallback, useEffect, useState } from "react";
import type { GeolocationState } from "@/types/mobility";

const INITIAL_STATE: GeolocationState = { status: "idle", coordinates: null };
let sessionState: GeolocationState = INITIAL_STATE;

export function useGeolocation() {
  const [state, setReactState] = useState<GeolocationState>(sessionState);

  const setState = useCallback((next: GeolocationState | ((current: GeolocationState) => GeolocationState)) => {
    setReactState((current) => {
      const resolved = typeof next === "function" ? next(current) : next;
      sessionState = resolved;
      return resolved;
    });
  }, []);

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
          status:
            error.code === error.PERMISSION_DENIED
              ? "denied"
              : error.code === error.TIMEOUT
                ? "timeout"
                : "unavailable",
          coordinates: null,
        });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 },
    );
  }, [setState]);

  useEffect(() => {
    if (state.status !== "idle" || !("permissions" in navigator)) return;
    void navigator.permissions.query({ name: "geolocation" }).then((permission) => {
      if (permission.state === "granted") requestLocation();
    }).catch(() => undefined);
  }, [requestLocation, state.status]);

  return { ...state, requestLocation };
}
