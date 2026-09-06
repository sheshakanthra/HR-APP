import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, ChevronDown } from "lucide-react";
import type { OrgNode } from "../../lib/types";
import { Avatar } from "../ui";
import { inferTier, TIER_STYLES } from "../../lib/orgTiers";
import ConnectorSvg from "./ConnectorSvg";

const CONNECTOR_TINT: Record<string, string> = {
  executive: "stroke-accent-2/50",
  leadership: "stroke-accent-2/30",
  manager: "stroke-border",
  ic: "stroke-border/60",
};

const BADGE_TINT: Record<string, string> = {
  executive: "text-accent-2 bg-accent-2/10 border-accent-2/40",
  leadership: "text-accent-2 bg-accent-2/10 border-accent-2/30",
  manager: "text-accent bg-accent/10 border-accent/30",
  ic: "text-accent bg-accent/10 border-accent/30",
};

export default function OrgTreeNode({ node, depth }: { node: OrgNode; depth: number }) {
  // Only the root auto-opens. Unlike the flat list view, chart-view rows lay
  // siblings out horizontally — some department heads in this org have 20+
  // direct reports with no intermediate manager tier, so auto-opening every
  // depth-1 node (mirroring the list view's depth<2) fans out into an
  // unusably wide canvas. One open tier plus collapsed-badge affordances
  // keeps the default view navigable.
  const [open, setOpen] = useState(depth === 0);
  const hasReports = node.reports.length > 0;
  const tier = inferTier(node.title, depth);
  const style = TIER_STYLES[tier];

  const cardInner = (
    <>
      <div className="flex items-center gap-2">
        <Avatar first={node.first_name} last={node.last_name} size={style.avatar} />
        <div className="min-w-0 flex-1">
          <div className={`truncate ${style.name}`}>
            {node.first_name} {node.last_name}
          </div>
          <div className={`truncate ${style.title}`}>{node.title}</div>
        </div>
        {hasReports && (
          <Link
            to={`/directory/${node.id}`}
            onClick={(e) => e.stopPropagation()}
            className="shrink-0 rounded p-0.5 text-muted hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
            aria-label={`View ${node.first_name} ${node.last_name}'s profile`}
          >
            <ArrowUpRight size={13} />
          </Link>
        )}
      </div>
      {hasReports && !open && (
        <span
          className={`mt-2 inline-flex items-center gap-1 rounded border px-1.5 py-0.5 font-mono text-[10px] ${BADGE_TINT[tier]}`}
        >
          <ChevronDown size={10} className="-rotate-90" />
          {node.reports.length} report{node.reports.length === 1 ? "" : "s"}
        </span>
      )}
    </>
  );

  return (
    <div className="flex flex-col items-center" data-open={open ? "true" : "false"}>
      {hasReports ? (
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className={`rounded-md border text-left transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 ${style.card} ${style.padding} ${style.minWidth}`}
        >
          {cardInner}
        </button>
      ) : (
        <Link
          to={`/directory/${node.id}`}
          className={`block rounded-md border text-left transition-colors duration-150 hover:border-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 ${style.card} ${style.padding} ${style.minWidth}`}
        >
          {cardInner}
        </Link>
      )}

      {hasReports && (
        <div
          className="grid transition-[grid-template-rows] duration-300 ease-out"
          // maxWidth is the load-bearing part here, not just gridTemplateRows:
          // grid/flex track sizing measures a collapsed row's max-content
          // width regardless of its 0fr height, so every closed branch would
          // otherwise still reserve full horizontal space for its (hidden)
          // subtree — capping width to 0 when closed is what actually keeps
          // the canvas from fanning out to the width of every branch at once.
          style={{ gridTemplateRows: open ? "1fr" : "0fr", maxWidth: open ? undefined : 0 }}
        >
          <div className="overflow-hidden">
            {/* relative + pt-6 reserves space for the absolutely-positioned
                connector, so the row below determines this wrapper's width
                (not the other way round) — avoids a shrink-to-fit/percentage
                sizing loop between the connector and the row it overlays. */}
            <div className="relative pt-6">
              <ConnectorSvg
                childCount={node.reports.length}
                tint={CONNECTOR_TINT[tier]}
                className="absolute inset-x-0 top-0 h-6 w-full"
              />
              <div className="flex items-start">
                {node.reports.map((r) => (
                  <div key={r.id} className="flex justify-center px-3 pb-2">
                    <OrgTreeNode node={r} depth={depth + 1} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
