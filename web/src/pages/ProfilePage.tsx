import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Mail, MapPin, Building2, CalendarDays, ShieldAlert } from "lucide-react";
import { useProfile } from "../lib/queries";
import { ApiError } from "../lib/api";
import { Avatar, Card, EmptyState, Spinner } from "../components/ui";

export default function ProfilePage() {
  const { id } = useParams();
  const { data, isLoading, error } = useProfile(Number(id));

  if (isLoading) return <Spinner label="loading profile…" />;

  if (error) {
    const forbidden = error instanceof ApiError && error.status === 403;
    return (
      <div>
        <BackLink />
        <EmptyState>
          <ShieldAlert className="mx-auto mb-2 text-amber-300" size={22} />
          {forbidden
            ? "You can view this person's directory card but not their full record."
            : "Employee not found."}
        </EmptyState>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <BackLink />
      <div className="mb-6 flex items-center gap-4">
        <span className="flex h-16 w-16 items-center justify-center rounded-full border border-accent/30 bg-accent/10 font-mono text-lg text-accent">
          {data.first_name[0]}
          {data.last_name[0]}
        </span>
        <div>
          <h1 className="text-2xl font-semibold">
            {data.first_name} {data.last_name}
          </h1>
          <p className="font-mono text-sm text-muted">{data.title}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5">
          <h2 className="mb-4 font-mono text-xs uppercase tracking-widest text-muted">Details</h2>
          <dl className="space-y-3 text-sm">
            <Row icon={Mail} label="Email" value={data.work_email} />
            <Row icon={Building2} label="Department" value={data.department_name ?? "—"} />
            <Row icon={MapPin} label="Location" value={data.location} />
            <Row icon={CalendarDays} label="Hire date" value={data.hire_date} />
            <Row icon={ShieldAlert} label="Status" value={data.employment_status} />
          </dl>
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 font-mono text-xs uppercase tracking-widest text-muted">
            Reporting
          </h2>
          {data.manager ? (
            <Link
              to={`/directory/${data.manager.id}`}
              className="mb-4 flex cursor-pointer items-center gap-3 rounded-md border border-border p-3 hover:border-accent/50"
            >
              <Avatar first={data.manager.first_name} last={data.manager.last_name} />
              <div>
                <div className="text-sm">
                  {data.manager.first_name} {data.manager.last_name}
                </div>
                <div className="font-mono text-xs text-muted">{data.manager.title}</div>
              </div>
            </Link>
          ) : (
            <p className="mb-4 font-mono text-xs text-muted">No manager (top of org).</p>
          )}

          <h3 className="mb-2 font-mono text-[11px] uppercase tracking-widest text-muted">
            Direct reports ({data.direct_reports.length})
          </h3>
          <div className="space-y-2">
            {data.direct_reports.map((r) => (
              <Link
                key={r.id}
                to={`/directory/${r.id}`}
                className="flex cursor-pointer items-center gap-3 rounded-md border border-border p-2 hover:border-accent/50"
              >
                <Avatar first={r.first_name} last={r.last_name} />
                <div className="min-w-0">
                  <div className="truncate text-sm">
                    {r.first_name} {r.last_name}
                  </div>
                  <div className="truncate font-mono text-xs text-muted">{r.title}</div>
                </div>
              </Link>
            ))}
            {data.direct_reports.length === 0 && (
              <p className="font-mono text-xs text-muted">None.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/directory"
      className="mb-4 inline-flex cursor-pointer items-center gap-1 font-mono text-sm text-muted hover:text-accent"
    >
      <ArrowLeft size={15} /> directory
    </Link>
  );
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Mail;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <Icon size={15} className="text-accent/70" />
      <dt className="w-24 font-mono text-xs text-muted">{label}</dt>
      <dd className="text-slate-200">{value}</dd>
    </div>
  );
}
