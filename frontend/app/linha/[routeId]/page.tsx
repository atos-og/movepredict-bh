import { LineDetails } from "@/components/roadmap/line-details";

export function generateStaticParams() {
  return [{ routeId: "989341" }];
}

export default async function LinePage({ params }: { params: Promise<{ routeId: string }> }) { const { routeId } = await params; return <LineDetails routeId={decodeURIComponent(routeId)} />; }
