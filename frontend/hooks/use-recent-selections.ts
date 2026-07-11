"use client";

import { useCallback, useEffect, useState } from "react";
import type { RecentSelection } from "@/types/mobility";

const STORAGE_KEY = "movepredict:recent-selections";

export function useRecentSelections(limit = 4) {
  const [items, setItems] = useState<RecentSelection[]>([]);

  useEffect(() => {
    const loadStoredItems = window.setTimeout(() => {
      try {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored) setItems((JSON.parse(stored) as RecentSelection[]).slice(0, limit));
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }, 0);
    return () => window.clearTimeout(loadStoredItems);
  }, [limit]);

  const remember = useCallback(
    (selection: RecentSelection) => {
      setItems((current) => {
        const next = [
          selection,
          ...current.filter((item) => item.kind !== selection.kind || item.id !== selection.id),
        ].slice(0, limit);
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    },
    [limit],
  );

  return { items, remember };
}
