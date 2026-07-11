"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { JourneyScreen } from "@/components/roadmap/journey-screen";

function RouteContent() {
  const params = useSearchParams();
  const preview = (process.env.NODE_ENV !== "production" || process.env.NEXT_PUBLIC_ENABLE_VISUAL_PREVIEW === "true") && params.get("preview") === "1";
  return <JourneyScreen preview={preview} details={params.get("details") === "1"} />;
}

export default function RoutePage() {
  return <Suspense><RouteContent /></Suspense>;
}
