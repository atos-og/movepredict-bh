import { ActiveJourney } from "@/components/roadmap/active-journey";

export default async function JourneyPage({ searchParams }: { searchParams: Promise<{ preview?: string; map?: string }> }) {
  const params = await searchParams;
  const preview = process.env.NODE_ENV !== "production" && params.preview === "1";
  return <ActiveJourney preview={preview} map={params.map === "1"} />;
}
