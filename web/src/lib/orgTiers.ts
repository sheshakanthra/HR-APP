export type Tier = "executive" | "leadership" | "manager" | "ic";

export function inferTier(title: string, depth: number): Tier {
  const t = title.trim();
  if (/^chief\s+.*officer$/i.test(t)) return "executive";
  if (/\b(vp|vice president|director|head)\b/i.test(t)) return "leadership";
  if (/\b(manager|lead)\b/i.test(t)) return "manager";
  if (/,/.test(t)) return "ic";
  // fallback only when the title doesn't match the known vocabulary
  if (depth === 0) return "executive";
  if (depth === 1) return "leadership";
  if (depth <= 3) return "manager";
  return "ic";
}

interface TierStyle {
  card: string;
  avatar: "sm" | "md";
  padding: string;
  name: string;
  title: string;
  badge: string;
  minWidth: string;
}

export const TIER_STYLES: Record<Tier, TierStyle> = {
  executive: {
    card: "bg-surface-2 border-accent-2/50",
    avatar: "md",
    padding: "p-4",
    name: "text-base font-semibold text-slate-100",
    title: "font-mono text-xs text-accent-2",
    badge: "text-accent-2 bg-accent-2/10 border-accent-2/40",
    minWidth: "min-w-[180px]",
  },
  leadership: {
    card: "bg-surface border-accent-2/30",
    avatar: "md",
    padding: "p-3.5",
    name: "text-sm font-medium text-slate-100",
    title: "font-mono text-xs text-muted",
    badge: "text-accent-2 bg-accent-2/10 border-accent-2/30",
    minWidth: "min-w-[170px]",
  },
  manager: {
    card: "bg-surface border-border",
    avatar: "sm",
    padding: "p-3",
    name: "text-sm text-slate-100",
    title: "font-mono text-[11px] text-muted",
    badge: "text-accent bg-accent/10 border-accent/30",
    minWidth: "min-w-[150px]",
  },
  ic: {
    card: "bg-bg border-border/60",
    avatar: "sm",
    padding: "p-2",
    name: "text-xs text-slate-200",
    title: "font-mono text-[10px] text-muted",
    badge: "text-accent bg-accent/10 border-accent/30",
    minWidth: "min-w-[140px]",
  },
};
