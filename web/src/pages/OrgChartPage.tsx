import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, ChevronDown, List, GitBranch } from "lucide-react";
import { useOrgChart } from "../lib/queries";
import type { OrgNode } from "../lib/types";
import { Card, Spinner } from "../components/ui";
import OrgTreeNode from "../components/org/OrgTreeNode";

function Node({ node, depth }: { node: OrgNode; depth: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasReports = node.reports.length > 0;

  return (
    <div>
      <div
        className="flex items-center gap-2 rounded-md py-1"
        style={{ paddingLeft: depth * 18 }}
      >
        {hasReports ? (
          <button
            onClick={() => setOpen((o) => !o)}
            className="cursor-pointer rounded text-muted hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
          >
            {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
          </button>
        ) : (
          <span className="w-[15px]" />
        )}
        <Link
          to={`/directory/${node.id}`}
          className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
        >
          <span className="text-sm text-slate-100">
            {node.first_name} {node.last_name}
          </span>
          <span className="font-mono text-xs text-muted">· {node.title}</span>
          {hasReports && (
            <span className="font-mono text-[10px] text-accent/70">[{node.reports.length}]</span>
          )}
        </Link>
      </div>
      {open &&
        node.reports.map((r) => <Node key={r.id} node={r} depth={depth + 1} />)}
    </div>
  );
}

export default function OrgChartPage() {
  const { data, isLoading } = useOrgChart();
  const [view, setView] = useState<"list" | "chart">("list");
  const canvasRef = useRef<HTMLDivElement>(null);

  // The canvas centers its (possibly much wider than the viewport) content
  // via justify-center, which by default leaves the root scrolled out of
  // view on first paint — recenter the scroll position on the root instead
  // of making people hunt for it.
  useEffect(() => {
    if (view !== "chart" || !data?.length) return;
    const el = canvasRef.current;
    if (!el) return;
    el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2;
  }, [view, data]);

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="mb-1 text-2xl font-semibold">Org Chart</h1>
          <p className="font-mono text-sm text-muted">Reporting hierarchy</p>
        </div>
        <div className="flex gap-1 rounded-md border border-border p-1">
          <button
            onClick={() => setView("list")}
            className={`flex cursor-pointer items-center gap-1.5 rounded px-2.5 py-1 font-mono text-xs transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 ${
              view === "list" ? "bg-accent/10 text-accent" : "text-muted hover:text-slate-100"
            }`}
          >
            <List size={13} /> List
          </button>
          <button
            onClick={() => setView("chart")}
            className={`flex cursor-pointer items-center gap-1.5 rounded px-2.5 py-1 font-mono text-xs transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 ${
              view === "chart" ? "bg-accent/10 text-accent" : "text-muted hover:text-slate-100"
            }`}
          >
            <GitBranch size={13} /> Chart
          </button>
        </div>
      </div>

      {isLoading ? (
        <Spinner label="building tree…" />
      ) : view === "list" ? (
        <Card className="p-4">
          {data?.map((root) => <Node key={root.id} node={root} depth={0} />)}
        </Card>
      ) : (
        <div ref={canvasRef} className="overflow-x-auto rounded-lg border border-border bg-bg p-8">
          <div className="flex min-w-max justify-center gap-10">
            {data?.map((root) => <OrgTreeNode key={root.id} node={root} depth={0} />)}
          </div>
        </div>
      )}
    </div>
  );
}
