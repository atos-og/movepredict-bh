"use client";

import { useCallback, useEffect, useState } from "react";
import type { RecentSelection } from "@/types/mobility";

const STORAGE_KEY = "movepredict:favorites";

export function useFavorites() {
  const [items, setItems] = useState<RecentSelection[]>([]);

  useEffect(() => {
    const loadStoredItems = window.setTimeout(() => {
      try {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored) setItems(JSON.parse(stored) as RecentSelection[]);
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }, 0);
    return () => window.clearTimeout(loadStoredItems);
  }, []);

  const isFavorite = useCallback(
    (selection: RecentSelection) => items.some((item) => item.kind === selection.kind && item.id === selection.id),
    [items],
  );

  const toggle = useCallback((selection: RecentSelection) => {
    setItems((current) => {
      const exists = current.some((item) => item.kind === selection.kind && item.id === selection.id);
      const next = exists
        ? current.filter((item) => item.kind !== selection.kind || item.id !== selection.id)
        : [selection, ...current];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { items, isFavorite, toggle };
}
