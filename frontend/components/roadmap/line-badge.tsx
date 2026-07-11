export function LineBadge({ value, color = "#0d3977", tone = "navy" }: { value: string; color?: string; tone?: "navy" | "green" | "orange" | "pink" }) {
  return <span className={`roadmap-line-badge ${tone}`} style={{ "--badge-color": color } as React.CSSProperties}>{value}</span>;
}
