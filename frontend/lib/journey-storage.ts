import type { Coordinates, GeocodedDestination, JourneyPlan } from "@/types/mobility";

const ACTIVE_KEY = "movepredict.active-journey.v1";
const SAVED_KEY = "movepredict.saved-journeys.v1";

export type StoredJourney = {
  plan: JourneyPlan;
  origin: Coordinates;
  destination: GeocodedDestination;
  savedAt: string;
};

export function storeActiveJourney(journey: StoredJourney): void {
  localStorage.setItem(ACTIVE_KEY, JSON.stringify(journey));
}

export function readActiveJourney(): StoredJourney | null {
  return readStored(ACTIVE_KEY);
}

export function clearActiveJourney(): void {
  localStorage.removeItem(ACTIVE_KEY);
}

export function saveJourneyOffline(journey: StoredJourney): void {
  const current = readSavedJourneys().filter((item) => item.plan.id !== journey.plan.id);
  localStorage.setItem(SAVED_KEY, JSON.stringify([journey, ...current].slice(0, 8)));
}

export function readSavedJourneys(): StoredJourney[] {
  const value = readStored<StoredJourney[]>(SAVED_KEY);
  return Array.isArray(value) ? value : [];
}

export function readSavedJourney(planId: string): StoredJourney | null {
  return readSavedJourneys().find((item) => item.plan.id === planId) || null;
}

function readStored<T = StoredJourney>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : null;
  } catch {
    return null;
  }
}
