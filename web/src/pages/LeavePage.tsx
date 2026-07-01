import { FormEvent, useState } from "react";
import { CalendarPlus, X } from "lucide-react";
import {
  useCancelLeave,
  useLeaveTypes,
  useMyBalance,
  useMyRequests,
  useSubmitLeave,
} from "../lib/queries";
import { ApiError } from "../lib/api";
import { Button, Card, EmptyState, Input, SectionTitle, Spinner, StatusBadge } from "../components/ui";

export default function LeavePage() {
  const { data: balances, isLoading: balLoading } = useMyBalance();
  const { data: types } = useLeaveTypes();
  const { data: requests, isLoading: reqLoading } = useMyRequests();
  const submit = useSubmitLeave();
  const cancel = useCancelLeave();

  const [typeId, setTypeId] = useState<number | "">("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (typeId === "" || !start || !end) {
      setError("Pick a leave type and dates.");
      return;
    }
    try {
      await submit.mutateAsync({
        leave_type_id: Number(typeId),
        start_date: start,
        end_date: end,
        reason,
      });
      setStart("");
      setEnd("");
      setReason("");
      setTypeId("");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Submission failed");
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">My Leave</h1>
      <p className="mb-6 font-mono text-sm text-muted">Balances, requests & submission</p>

      {/* Balances */}
      <SectionTitle>Balances</SectionTitle>
      {balLoading ? (
        <Spinner />
      ) : (
        <div className="mb-8 grid gap-3 sm:grid-cols-3">
          {balances?.map((b) => (
            <Card key={b.leave_type_id} className="p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-muted">
                {b.leave_type_name}
              </div>
              <div className="mt-2 font-mono text-3xl text-accent">{b.available.toFixed(1)}</div>
              <div className="mt-1 font-mono text-[11px] text-muted">
                {b.available.toFixed(1)} available · {b.used.toFixed(1)} used · {b.accrued.toFixed(1)}{" "}
                accrued
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Submit form */}
        <div>
          <SectionTitle>Request time off</SectionTitle>
          <Card className="p-5">
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block font-mono text-xs text-muted">Leave type</label>
                <select
                  value={typeId}
                  onChange={(e) => setTypeId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full cursor-pointer rounded-md border border-border bg-bg px-3 py-2 text-sm text-slate-100 focus:border-accent/60 focus:outline-none"
                >
                  <option value="">Select…</option>
                  {types?.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block font-mono text-xs text-muted">Start</label>
                  <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
                </div>
                <div>
                  <label className="mb-1 block font-mono text-xs text-muted">End</label>
                  <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono text-xs text-muted">Reason (optional)</label>
                <Input value={reason} onChange={(e) => setReason(e.target.value)} />
              </div>
              {error && <p className="font-mono text-xs text-rose-400">{error}</p>}
              <Button type="submit" disabled={submit.isPending} className="flex items-center gap-2">
                <CalendarPlus size={15} />
                {submit.isPending ? "Submitting…" : "Submit for approval"}
              </Button>
              <p className="font-mono text-[11px] text-muted">
                Requests route to your manager. Approval is always human.
              </p>
            </form>
          </Card>
        </div>

        {/* History */}
        <div>
          <SectionTitle>History</SectionTitle>
          {reqLoading ? (
            <Spinner />
          ) : !requests || requests.length === 0 ? (
            <EmptyState>No leave requests yet.</EmptyState>
          ) : (
            <div className="space-y-2">
              {requests.map((r) => (
                <Card key={r.id} className="flex items-center justify-between p-3">
                  <div>
                    <div className="flex items-center gap-2 text-sm">
                      <span>{r.leave_type_name}</span>
                      <StatusBadge status={r.status} />
                      {r.created_via_agent && (
                        <span className="font-mono text-[10px] text-accent/70">via agent</span>
                      )}
                    </div>
                    <div className="font-mono text-xs text-muted">
                      {r.start_date} → {r.end_date} · {r.days} day(s)
                    </div>
                  </div>
                  {(r.status === "pending" || r.status === "approved") && (
                    <button
                      onClick={() => cancel.mutate(r.id)}
                      className="flex cursor-pointer items-center gap-1 rounded border border-border px-2 py-1 font-mono text-[11px] text-muted hover:border-rose-400/50 hover:text-rose-300"
                    >
                      <X size={12} /> cancel
                    </button>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
