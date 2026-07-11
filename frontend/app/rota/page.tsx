import { JourneyScreen } from "@/components/roadmap/journey-screen";

export default async function RoutePage({ searchParams }: { searchParams: Promise<{ preview?: string; details?: string }> }) {
  const params = await searchParams;
  const preview = process.env.NODE_ENV !== "production" && params.preview === "1";
  return <JourneyScreen preview={preview} details={params.details === "1"} />;
}
