import { Terminal, ShieldCheck, Users, CalendarClock, BookText, Bot } from "lucide-react";

// Milestone 1 placeholder shell. Real routes/pages land in Milestone 3+.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const modules = [
  { icon: Users, label: "Directory & Org Chart", status: "Milestone 3" },
  { icon: CalendarClock, label: "Leave / PTO", status: "Milestone 3" },
  { icon: BookText, label: "Policy Knowledge Base", status: "Milestone 4" },
  { icon: Bot, label: "AI HR Agent", status: "Milestone 5" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-bg text-slate-200">
      <header className="border-b border-border px-6 py-4 flex items-center gap-3">
        <Terminal className="text-accent" size={22} />
        <span className="font-mono font-bold tracking-wide text-accent">PeopleDesk</span>
        <span className="text-muted text-xs font-mono ml-2">// HRMS + core AI agent</span>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-16">
        <div className="flex items-center gap-2 text-accent font-mono text-sm mb-2">
          <ShieldCheck size={16} /> Milestone 1 — scaffold online
        </div>
        <h1 className="text-2xl font-semibold mb-6">Backbone is up.</h1>
        <p className="text-muted mb-8 font-mono text-sm">
          API base: <span className="text-accent">{API_BASE}</span>
        </p>

        <ul className="grid gap-3">
          {modules.map((m) => (
            <li
              key={m.label}
              className="flex items-center justify-between border border-border rounded-lg bg-surface px-4 py-3"
            >
              <span className="flex items-center gap-3">
                <m.icon size={18} className="text-accent" />
                {m.label}
              </span>
              <span className="font-mono text-xs text-muted">{m.status}</span>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
