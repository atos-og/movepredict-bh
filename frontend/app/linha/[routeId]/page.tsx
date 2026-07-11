import { LineDetails } from "@/components/roadmap/line-details";
export default async function LinePage({ params }: { params: Promise<{ routeId: string }> }) { const { routeId } = await params; return <LineDetails routeId={decodeURIComponent(routeId)} />; }
