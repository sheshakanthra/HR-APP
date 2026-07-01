import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Terminal,
  Users,
  Network,
  CalendarClock,
  CheckSquare,
  Bot,
  LogOut,
} from "lucide-react";
import { useAuth } from "../lib/auth";

const NAV = [
  { to: "/directory", label: "Directory", icon: Users, minRole: "employee" as const },
  { to: "/org-chart", label: "Org Chart", icon: Network, minRole: "employee" as const },
  { to: "/leave", label: "My Leave", icon: CalendarClock, minRole: "employee" as const },
  { to: "/approvals", label: "Approvals", icon: CheckSquare, minRole: "manager" as const },
  { to: "/agent", label: "AI Assistant", icon: Bot, minRole: "employee" as const },
];

export default function Layout() {
  const { me, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen bg-bg text-slate-200">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-surface">
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
          <Terminal className="text-accent" size={20} />
          <span className="font-mono font-bold tracking-wide text-accent">PeopleDesk</span>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.filter((n) => hasRole(n.minRole)).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors duration-150 ${
                  isActive
                    ? "bg-accent/10 text-accent"
                    : "text-slate-300 hover:bg-white/5 hover:text-slate-100"
                }`
              }
            >
              <n.icon size={17} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <div className="mb-2 px-2 font-mono text-xs text-muted">
            <div className="truncate text-slate-300">{me?.user.email}</div>
            <div className="text-accent">{me?.user.rbac_role}</div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-300 transition-colors duration-150 hover:bg-white/5 hover:text-rose-300"
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
