import { ReactNode } from "react";
import type { LeaveStatus } from "../lib/types";

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-muted font-mono text-sm">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      {label ?? "loading…"}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-border bg-surface ${className}`}>{children}</div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="font-mono text-xs uppercase tracking-widest text-muted mb-3">{children}</h2>
  );
}

const STATUS_STYLES: Record<LeaveStatus, string> = {
  pending: "text-amber-300 border-amber-400/40 bg-amber-400/10",
  approved: "text-accent border-accent/40 bg-accent/10",
  rejected: "text-rose-300 border-rose-400/40 bg-rose-400/10",
  cancelled: "text-slate-400 border-slate-500/40 bg-slate-500/10",
};

export function StatusBadge({ status }: { status: LeaveStatus }) {
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wider ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: {
  children: ReactNode;
  variant?: "primary" | "ghost" | "danger";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const styles = {
    primary: "bg-accent text-black hover:bg-accent/90 disabled:opacity-40",
    ghost: "border border-border text-slate-200 hover:border-accent/60 hover:text-accent",
    danger: "border border-rose-400/40 text-rose-300 hover:bg-rose-400/10",
  }[variant];
  return (
    <button
      className={`cursor-pointer rounded-md px-3 py-1.5 font-mono text-sm transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:cursor-not-allowed ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-slate-100 placeholder:text-muted focus:border-accent/60 focus:outline-none focus:ring-1 focus:ring-accent/40 ${props.className ?? ""}`}
    />
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-border p-8 text-center font-mono text-sm text-muted">
      {children}
    </div>
  );
}

export function Avatar({ first, last }: { first: string; last: string }) {
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-accent/30 bg-accent/10 font-mono text-xs text-accent">
      {first[0]}
      {last[0]}
    </span>
  );
}
