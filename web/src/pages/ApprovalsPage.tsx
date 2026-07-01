import { useState } from "react";
import { Check, X, Clock } from "lucide-react";
import { useApprovalQueue, useDecideLeave } from "../lib/queries";
import { Avatar, Button, Card, EmptyState, Input, Spinner } from "../components/ui";

export default function ApprovalsPage() {
  const { data, isLoading } = useApprovalQueue();
  const decide = useDecideLeave();
  const [notes, setNotes] = useState<Record<number, string>>({});

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Approval Queue</h1>
      <p className="mb-6 font-mono text-sm text-muted">Pending leave from your team</p>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState>
          <Clock className="mx-auto mb-2 text-muted" size={22} />
          Nothing awaiting your decision.
        </EmptyState>
      ) : (
        <div className="space-y-3">
          {data.map((r) => (
            <Card key={r.id} className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <Avatar
                    first={r.employee?.first_name ?? "?"}
                    last={r.employee?.last_name ?? "?"}
                  />
                  <div>
                    <div className="text-sm">
                      {r.employee?.first_name} {r.employee?.last_name}
                    </div>
                    <div className="font-mono text-xs text-muted">
                      {r.leave_type_name} · {r.start_date} → {r.end_date} · {r.days} day(s)
                    </div>
                    {r.reason && (
                      <div className="mt-1 font-mono text-xs text-slate-400">“{r.reason}”</div>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Input
                  placeholder="Optional note…"
                  value={notes[r.id] ?? ""}
                  onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                  className="max-w-xs"
                />
                <Button
                  variant="primary"
                  disabled={decide.isPending}
                  onClick={() => decide.mutate({ id: r.id, approve: true, note: notes[r.id] ?? "" })}
                  className="flex items-center gap-1"
                >
                  <Check size={14} /> Approve
                </Button>
                <Button
                  variant="danger"
                  disabled={decide.isPending}
                  onClick={() => decide.mutate({ id: r.id, approve: false, note: notes[r.id] ?? "" })}
                  className="flex items-center gap-1"
                >
                  <X size={14} /> Reject
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
