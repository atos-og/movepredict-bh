import { Suspense } from "react";
import { TransitExplorer } from "@/components/transit-explorer";

export default function ExplorePage() {
  return <Suspense><TransitExplorer /></Suspense>;
}
