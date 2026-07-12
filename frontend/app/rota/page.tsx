"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { JourneyScreen } from "@/components/roadmap/journey-screen";

function RouteContent() {
  const params = useSearchParams();
  const preview = (process.env.NODE_ENV !== "production" || process.env.NEXT_PUBLIC_ENABLE_VISUAL_PREVIEW === "true") && params.get("preview") === "1";
  const latitude = Number(params.get("lat"));
  const longitude = Number(params.get("lon"));
  const destination = params.get("destination");
  const selectedDestination = destination && Number.isFinite(latitude) && Number.isFinite(longitude)
    ? { id: `${latitude},${longitude}`, kind: "destination" as const, label: destination, description: "Belo Horizonte - MG", coordinates: { latitude, longitude } }
    : null;
  return <JourneyScreen preview={preview} details={params.get("details") === "1"} destination={selectedDestination} />;
}

export default function RoutePage() {
  return <Suspense><RouteContent /></Suspense>;
}
