"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ArrivalPrediction, RealtimeMeta, VehiclePosition } from "@/types/realtime";

export type RealtimeState = "loading" | "live" | "empty" | "stale" | "offline";

export function useVehicles(routeId?: string, intervalMs = 20_000) {
  const [vehicles, setVehicles] = useState<VehiclePosition[]>([]);
  const [meta, setMeta] = useState<RealtimeMeta | null>(null);
  const [state, setState] = useState<RealtimeState>("loading");
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await api.listVehicles(routeId);
      setVehicles(response.data);
      setMeta(response.meta);
      setState(response.meta.stale ? (response.data.length ? "stale" : "empty") : "live");
      setMessage(null);
    } catch (error) {
      setState("offline");
      setMessage(
        error instanceof ApiError && error.status === 503
          ? "Dados em tempo real temporariamente indisponiveis."
          : "Sem conexao com o monitoramento ao vivo.",
      );
    }
  }, [routeId]);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), intervalMs);
    const onVisibility = () => { if (document.visibilityState === "visible") void refresh(); };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [intervalMs, refresh]);

  return { vehicles, meta, state, message, refresh };
}

export function useArrivals(stopId: string | null, intervalMs = 20_000) {
  const [arrivals, setArrivals] = useState<ArrivalPrediction[]>([]);
  const [state, setState] = useState<RealtimeState>(stopId ? "loading" : "empty");

  const refresh = useCallback(async () => {
    if (!stopId) return;
    try {
      const response = await api.listArrivals(stopId);
      setArrivals(response.data);
      setState(
        response.meta.stale
          ? response.data.length ? "stale" : "empty"
          : response.data.length ? "live" : "empty",
      );
    } catch {
      setState("offline");
    }
  }, [stopId]);

  useEffect(() => {
    if (!stopId) return;
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), intervalMs);
    return () => { window.clearTimeout(initial); window.clearInterval(timer); };
  }, [intervalMs, refresh, stopId]);

  return { arrivals, state, refresh };
}
