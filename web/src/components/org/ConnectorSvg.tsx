interface ConnectorSvgProps {
  childCount: number;
  tint?: string;
  className?: string;
}

export default function ConnectorSvg({ childCount, tint = "stroke-border", className = "" }: ConnectorSvgProps) {
  if (childCount <= 0) return null;

  const xs = Array.from({ length: childCount }, (_, i) => ((i + 0.5) / childCount) * 100);

  const paths: string[] = [];
  if (childCount === 1) {
    paths.push("M 50 0 V 24");
  } else {
    paths.push("M 50 0 V 12");
    paths.push(`M ${xs[0]} 12 H ${xs[xs.length - 1]}`);
    for (const x of xs) paths.push(`M ${x} 12 V 24`);
  }

  return (
    <svg
      viewBox="0 0 100 24"
      preserveAspectRatio="none"
      className={`org-connector pointer-events-none ${tint} ${className}`}
      aria-hidden="true"
    >
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" strokeWidth={1} vectorEffect="non-scaling-stroke" pathLength={1} />
      ))}
    </svg>
  );
}
