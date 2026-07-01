import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, ChevronDown } from "lucide-react";
import { useOrgChart } from "../lib/queries";
import type { OrgNode } from "../lib/types";
import { Card, Spinner } from "../components/ui";

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
            className="cursor-pointer text-muted hover:text-accent"
          >
            {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
          </button>
        ) : (
          <span className="w-[15px]" />
        )}
        <Link
          to={`/directory/${node.id}`}
          className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-white/5"
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

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Org Chart</h1>
      <p className="mb-6 font-mono text-sm text-muted">Reporting hierarchy</p>
      {isLoading ? (
        <Spinner label="building tree…" />
      ) : (
        <Card className="p-4">
          {data?.map((root) => <Node key={root.id} node={root} depth={0} />)}
        </Card>
      )}
    </div>
  );
}
