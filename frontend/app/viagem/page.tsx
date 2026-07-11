"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ActiveJourney } from "@/components/roadmap/active-journey";

function JourneyContent() {
  const params = useSearchParams();
  const preview = (process.env.NODE_ENV !== "production" || process.env.NEXT_PUBLIC_ENABLE_VISUAL_PREVIEW === "true") && params.get("preview") === "1";
  return <ActiveJourney preview={preview} map={params.get("map") === "1"} />;
}

export default function JourneyPage() {
  return <Suspense><JourneyContent /></Suspense>;
}
